import contextlib
import copy
import datetime
import django
from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils import timezone
import hashlib
from immutable import helpers
from immutable.exceptions import *
import json
import jsonschema
import uuid
import warnings


if not settings.USE_TZ == True:
    raise Exception("You are required to set USE_TZ=True in the django settings module, to support timezone-aware datetimes.")

def now():
    return timezone.now().isoformat()

class _BaseModel(models.Model):

    @classmethod
    def get_by_id(cls, _id):
        return cls.objects.get(_id=_id).downcast()

    @classmethod
    def get_by_definition(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        if data_obj.get('_id') is not None:
            return cls.get_by_id(data_obj.get('_id'))
        else:
            return None

    def get(self, field_name, downcast=True):
        try:
            field_value = getattr(self, field_name)
        except:
            return None
        if downcast:
            try:
                return field_value.downcast()
            except:
                pass
        return field_value

    def get_field_as_serializable(self, field_name):
        field_value = self.get(field_name)
        try:
            obj = field_value.to_obj()
        except:
            obj = field_value
        return helpers.NonserializableTypeConverter.convert(obj)

    def to_json(self):
        obj = self.to_obj()
        return self._obj_to_json(obj)


    def to_obj(self):
        model = self.downcast()
        return model._get_fields_as_obj()

    def to_serializable_obj(self):
        obj = self.to_obj()
        return helpers.NonserializableTypeConverter.convert(obj)

    @classmethod
    def _obj_to_json(cls, data_obj):
        return helpers.obj_to_json(data_obj)

    @classmethod
    def _json_to_obj(cls, data_json):
        return helpers.json_to_obj(data_json)

    @classmethod
    def _any_to_json(cls, data_obj_or_json):
        if isinstance(data, basestring):
            # Input appears to be JSON. Round trip to validate.
            data_obj = cls._json_to_obj(data_obj_or_json)
        else:
            data_obj = data_obj_or_json(data)
        return cls._obj_to_json(data_obj)

    @classmethod
    def _any_to_obj(cls, data):
        if isinstance(data, basestring):
            data_json = data
        else:
            # Input appears to be obj. Round trip to validate.
            data_json = cls._obj_to_json(data)
        return cls._json_to_obj(data_json)

    def _create_or_update_fields(self, data_obj):
        self.unsaved_many_to_many_related_objects = {}
        for (key, value) in data_obj.iteritems():
            self._create_or_update_field(key, value)
        self._set_datetime_updated()
        models.Model.save(self)
        self._save_many_to_many_related_objects()

    def _set_datetime_updated(self):
        # Override if needed
        pass

    def _save_many_to_many_related_objects(self):
        # Cannot create many-to-many relations until both models are
        # saved, but saving before adding other fields will raise
        # errors if those fields are required (null=False).
        # Now that all other fields are added and the model is saved,
        # we add many-to-many relations.
        while self.unsaved_many_to_many_related_objects:
            (key, children) = self.unsaved_many_to_many_related_objects.popitem()
            field = getattr(self, key)
            field.clear()
            for child in children:
                field.add(child)

    def _create_or_update_field(self, key, value):
        self._verify_field_is_not_a_parent(key)

        if self._is_array_field(key, value):
            self._create_or_update_many_to_many_field(key, value)
        elif self._is_foreign_key_field(key, value):
            self._create_or_update_foreign_key_field(key, value)
        else:
            self._create_or_update_scalar_field(key, value)        

    def _is_array_field(self, key, value):
        return isinstance(value, list)

    def _is_foreign_key_field(self, key, value):
        # A dict value may be either a model with a foreign key relation
        # or a JSON field. If JSON, we treat it as a scalar and let the 
        # JSON field model handle (de)serialization
        return isinstance(value, dict) and not self._is_json_field(key)

    def _is_json_field(self, field_name):
        if hasattr(self, 'JSON_FIELDS'):
            return field_name in self.JSON_FIELDS
        else:
            return False

    def _create_or_update_scalar_field(self, key, value):
        self._verify_field_is_a_scalar_field(key)
        if not hasattr(self, key):
            raise AttributeDoesNotExist("Attempted to set attribute %s on class %s, but the attribute does not exist." % (key, self.__class__))
        setattr(self, key, value)

    def _create_or_update_foreign_key_field(self, key, value):
        self._verify_field_is_a_foreign_key_field(key)
        if value is None:
            setattr(self, key, None)
            return
        else:
            child = self._create_or_update_child(key, value)
            setattr(self, key, child)

    def _create_or_update_many_to_many_field(self, key, valuelist):
        self._verify_field_is_many_to_many(key)
        # Cannot create many-to-many relation until model is
        # saved, so we keep a list to save later.
        unsaved_for_this_key = self.unsaved_many_to_many_related_objects.setdefault(key, [])

        if valuelist == [] or valuelist == None:
            # This will remove all many_to_many relations.
            return
        else:
            for value in valuelist:
                child = self._create_or_update_child(key, value)
                unsaved_for_this_key.append(child)

    def _create_or_update_child(self, key, value):
        Model = self._get_model_for_field_name(key, value)
        if value.get('_id') is None:
            child = Model.create(value)
        else:
            # Update existing model
            child = Model.objects.get(_id=value.get('_id'))
            if isinstance(child, MutableModel):
                child.update(value)
            elif isinstance(child, ImmutableModel):
                if child._id != ImmutableModel._calculate_unique_id(value):
                    # Error if update is not identical to existing ImmutableModel
                    raise AttemptedToUpdateImmutableError("Attempted to update an immutable object. Original: '%s'. Update: '%s'" % (child.to_obj(), value))
            else:
                raise Exception("All model classes must extend ImmutableModel or MutableModel. Neither class found for %s." % child)
        return child


    def _verify_field_is_not_a_parent(self, key):
        if self._is_field_a_parent(key):
            raise ParentNestedInChildException("Setting field %s on class %s is not permitted because the field is a parent. "
                                               "If this field is a foreign key child, add FOREIGN_KEY_CHILDREN = ['%s'] to the class definition of %s" 
                                               % (key, type(self), key, type(self)))

    def _verify_field_is_many_to_many(self, key):
        #TODO
        pass

    def _verify_field_is_a_foreign_key_field(self, key):
        #TODO
        pass

    def _verify_field_is_a_scalar_field(self, key):
        #TODO
        pass

    def _get_model_for_field_name(self, key, child_value):
        # Select the child model self.{key}
        field = self._meta.get_field(key)
        try:
            # Child related by foreign key
            Model = field.related.model
        except AttributeError as e:
            if isinstance(field, models.ManyToManyRel):
                # Child related by ManyToMany
                Model = field.model
            elif isinstance(field, models.ManyToOneRel):
                if not field.field.null:
                    raise ForeignKeyInChildError('A foreign key from child to parent must set null=True, since the child is defined first.')
                Model = field.related_model
                self._check_child_with_foreign_key_compatibility(Model)
            else:
                raise Exception("Unknown exception %s" % e.message)
        if Model._is_abstract(child_value):
            # If child model is abstract or is missing fields, look for a subclass that matches child_value
            child_fields = child_value.keys()
            Model = Model._select_best_subclass_model_by_fields(child_fields)
        self._check_child_compatibility(Model)
        return Model

    def _check_child_compatibility(self, Child):
        # Error if Child is not compatible with parent model (self)
        # This is overridden in ImmutableModel
        pass

    def _check_child_with_foreign_key_compatibility(self, Child):
        # Error if child cannot have foreign key to parent
        # This is overridden in ImmutableModel
        pass

    @classmethod
    def _is_abstract(cls, data_obj):
        # _do_all_fields_match will be true for multitable base classes
        # if data_obj contains fields not defined in the base class.
        return cls._meta.abstract or not cls._do_all_fields_match(data_obj)

    @classmethod
    def _select_best_subclass_model_by_fields(AbstractModel, fields):
        # This works for either abstract base class or multitable base class
        subclass_models = []
        for Model in django.apps.apps.get_models():
            if issubclass(Model, AbstractModel):
                subclass_models.append(Model)
        matching_models = []
        for Model in subclass_models:
            if Model._do_all_fields_match(fields):
                matching_models.append(Model)
        if len(matching_models) == 0:
            raise CouldNotFindSubclassError("Failed to find a subclass of abstract model %s that matches these fields: %s" % (AbstractModel, fields))
        elif len(matching_models) > 1:
            raise CouldNotFindUniqueSubclassError(
                "Failed to find a unique subclass of abstract model %s that matches these fields: %s. Multiple models matched: %s" 
                % (AbstractModel, fields, matching_models))
        else:
            return matching_models[0]
                
    @classmethod
    def _do_all_fields_match(cls, fields):
        model_fields = cls._meta.get_all_field_names()
        for field in fields:
            if field not in model_fields:
                return False
        return True
        
    def downcast(self):
        # If there is a subclass of this model with the same ID, return it.
        submodels = []
        for field in self._get_subclass_fields():
            try:
                model = getattr(self, field.name)
                if model._id == self._id:
                    submodels.append(model)
            except:
                #RelatedModelDoesNotExist
                pass
        if len(submodels) == 0:
            # No submodels for downcast.
            return self
        elif len(submodels) > 1:
            raise Exception("%s subclasses instances exist for abstract model %s. There should only be one." % (len(submodels), self))
        else:
            # Proceed recursively until no more downcasting is possible.
            return submodels[0].downcast()

    def _get_subclass_fields(self):
        subclass_fields = []
        for field in self._meta.get_fields():
            if isinstance(field, models.fields.related.OneToOneRel) and \
                    issubclass(field.related_model, self.__class__):
                subclass_fields.append(field)
        return subclass_fields

    def _get_fields_as_obj(self):
        obj = {}
        for field in self._meta.get_fields():
            field_obj = self._get_field_as_obj(field)
            if field_obj in [None, [], '']:
                continue
            obj[field.name] = field_obj
        return obj

    def _get_field_as_obj(self, field):
        if self._does_field_point_to_parent_or_base_class(field):
            # Ignore these fields in representation of model as an obj or json
            return None
        elif isinstance(field, models.fields.related.ManyToManyField):
            return self._get_many_to_many_field_as_obj(field)
        elif isinstance(field, models.fields.related.ForeignKey):
            return self._get_foreign_key_field_as_obj(field)
        elif isinstance(field, models.fields.related.ManyToOneRel):
            return self._get_many_to_one_field_as_obj(field)
        else:
            return getattr(self, field.name)

    def _does_field_point_to_parent_or_base_class(self, field):
        if isinstance(field, models.fields.related.ManyToManyRel) and \
                isinstance(self, field.model):
            # This is a ManyToMany defined on the parent model.
            return True
        elif isinstance(field, models.fields.related.OneToOneField) and \
                isinstance(self, field.related_model):
            # Points to a base class for this model.
            return True
        elif isinstance(field, models.fields.related.ManyToOneRel) :
            # and isinstance(self, field.model):
            # This is a ForeignKey. Return only if it is explicitly listed as
            # a child in self.FOREIGN_KEY_CHILDREN

            if self._is_field_a_foreign_key_child(field.name):
                # This is designated as a child model
                return False
            else:
                # This is not designated as a child. Ignore it.
                return True
        else:
            return False

    def _is_field_a_parent(self, field_name):
        # Field is a parent if it is a foreign key that is not listed in FOREIGN_KEY_CHILDREN
        # TODO: OR if the current class is listed in FOREIGN_KEY_CHILDREN of the field's model
        return self._is_field_a_foreign_key(field_name) and not self._is_field_a_foreign_key_child(field_name)

    def _is_field_a_foreign_key(self, field_name):
        return isinstance(self._meta.get_field(field_name), models.fields.related.ForeignKey)

    def _is_field_a_foreign_key_child(self, field_name):
        if hasattr(self, 'FOREIGN_KEY_CHILDREN'):
            return field_name in self.FOREIGN_KEY_CHILDREN
        else:
            return False

    def _get_foreign_key_field_as_obj(self, field):
        if not self._is_field_a_foreign_key_child(field.name):
            return None

        with warnings.catch_warnings():
            # Silence "use the 'create' or 'update' method" warning
            warnings.simplefilter("ignore")
            related_model = getattr(self, field.name)
        if related_model == None:
            return None
        else:
            return related_model.to_obj()

    def _get_many_to_one_field_as_obj(self, field):
        if not self._is_field_a_foreign_key_child(field.name):
            return None

        related_models = getattr(self, field.name).all()
        return [model.to_obj() for model in related_models]

    def _get_many_to_many_field_as_obj(self, field):
        related_model_list = getattr(self, field.name)
        related_model_obj = []
        for model in related_model_list.iterator():
            related_model_obj.append(model.to_obj())
        return related_model_obj

    def validate_model(self):
        pass

    class Meta:
        abstract = True

class MutableModel(_BaseModel):

    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime_created = models.DateTimeField(default=now)
    datetime_updated = models.DateTimeField(default=now)

    @classmethod
    def create(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        cls.validate_create_input(data_obj)
        Model = cls._select_best_subclass_model_by_fields(data_obj)
        with transaction.atomic():
            with warnings.catch_warnings():
                # Silence "use the 'create' or 'update' method" warning
                warnings.simplefilter("ignore")
                o = Model()
                o._create_or_update_fields(data_obj)
            o.validate_model()
        return o

    def update(self, update_json):
        update_obj = self._any_to_obj(update_json)
        self._verify_update_id_matches_model(update_obj.get('_id'))
        # Start with existing model and update any fields in update_json
        self.validate_patch_input(update_obj)
        model_obj = self.to_obj()
        model_obj.update(update_obj)
        with transaction.atomic():
            with warnings.catch_warnings():
                # Silence "use the 'create' or 'update' method" warning
                warnings.simplefilter("ignore")
                self._create_or_update_fields(model_obj)
            self.validate_model()
        return self

    @classmethod
    def validate_create_input(cls, data_obj):
        pass

    def validate_patch_input(self, data_obj):
        pass

    def _set_datetime_updated(self):
        self.datetime_updated = now()

    def _verify_update_id_matches_model(self, _id):
        if _id is None:
            return
        if str(_id) != str(self._id):
            raise UpdateIdMismatchError('Update does not match model. The update JSON gave an _id of "%s", but this model has _id "%s."'
                            % (_id, self._id))

    class Meta:
        abstract = True

class ImmutableModel(_BaseModel):

    _id = models.TextField(primary_key=True)

    @classmethod
    def create(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        cls.validate_create_input(data_obj)
        id_from_input = data_obj.get('_id')
        _id = cls._calculate_unique_id(data_obj)
        if id_from_input is not None:
            if id_from_input != _id:
                raise UniqueIdMismatchError("The input _id %s is out of sync with the hash of contents %s on model %s" %(id_from_input, data_obj, self.__class__))
        data_obj.update({'_id': _id})
        Model = cls._select_best_subclass_model_by_fields(data_obj)
        with transaction.atomic():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                o = Model()
                o._create_or_update_fields(data_obj)
            o.validate_model()
        return o

    @classmethod
    def validate_create_input(cls, data_obj):
        pass

    def save(self):
        raise NoSaveAllowedError("Immutable models cannot be saved after creation.")

    @classmethod
    def get_by_definition(cls, data_obj_or_json):
        id = cls._calculate_unique_id(data_obj_or_json)
        return cls.get_by_id(id)

    @classmethod
    def _calculate_unique_id(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        return helpers.IdCalculator(data_obj=data_obj, id_key='_id').get_id()

    def _check_child_compatibility(self, Child):
        if not issubclass(Child, ImmutableModel):
            raise MutableChildError("An ImmutableModel can only contain references to ImmutableModels. A %s cannot contain a %s." % (type(self), Child))

    def _check_child_with_foreign_key_compatibility(self, Child):
        raise ImmutableChildWithForeignKeyException('Immutable model %s has a foreign key to its parent. This is not allowed for immutable models.' % Child)

    def to_obj(self):
        obj = super(ImmutableModel, self).to_obj()
        self._verify_unique_id(obj)
        return obj

    def _verify_unique_id(self, obj):
        if not self._calculate_unique_id(obj) == self._id:
            raise UniqueIdMismatchError("The _id %s is out of sync with the hash of contents %s on model %s" %(self._id, obj, self.__class__))

    class Meta:
        abstract = True
