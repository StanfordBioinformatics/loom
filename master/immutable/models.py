import contextlib
import copy
import datetime
import django
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db import transaction
from django.utils import timezone
import hashlib
import json
import jsonschema
import uuid

from . import helpers
from .exceptions import *


if not settings.USE_TZ == True:
    raise Error("You are required to set USE_TZ=True in the django settings module, to support timezone-aware datetimes.")

def now():
    return timezone.now().isoformat()

class _BaseModel(models.Model):

    @classmethod
    def get_by_id(cls, _id):
        return cls.objects.get(_id=_id).downcast()

    @classmethod
    def get_by_definition(cls, data_obj_or_json):
        """Given a JSON or python structure as input,
        this method searches for that model in the database
        by id and, if found, returns the corresponding 
        ORM Model instance.
        """
        data_obj = cls._any_to_obj(data_obj_or_json)
        if data_obj.get('_id') is not None:
            model = cls.get_by_id(data_obj.get('_id'))
            from_db_obj = model.to_obj()
            from_db_json = cls._any_to_json(from_db_obj)
            data_json = cls._any_to_json(from_db_obj)
            if data_json != from_db_json:
                raise Error(
                    'Found a model with matching id but contents do not match. Input model %s does not match model from database %s.'
                    % (data_json, from_db_json))
            return model
        else:
            return None

    def get(self, field_name, downcast=True):
        """This convenience function looks up a child object
        by field and optionally downcasts it so that it will be 
        an instance of the lowest derived class.
        """
        # raises AttributeError
        field_value = getattr(self, field_name)
        if downcast:
            return field_value.downcast()
        else:
            return field_value
        
    def to_json(self):
        """Render Model instance as JSON
        """
        obj = self.to_obj()
        return self._obj_to_json(obj)

    def to_obj(self):
        """Render Model instance as a python structure.
        This method is recursive. Any non-serializable values
        are converted to their serializable form.
        """
        model = self.downcast()
        obj = {}
        for field in model._meta.get_fields():
            field_obj = model.get_field_as_obj(field)
            if field_obj in [None, [], '']:
                continue
            obj[field.name] = field_obj
        return obj

    @classmethod
    def _obj_to_json(cls, data_obj):
        """Render python structure representation of a model
        as a JSON representation.
        """
        return helpers.obj_to_json(data_obj)

    @classmethod
    def _json_to_obj(cls, data_json):
        """Render JSON representation of a model
        as a python structure.
        """
        return helpers.json_to_obj(data_json)

    @classmethod
    def _any_to_json(cls, data):
        """Accept either a JSON or a python structure and
        return a JSON
        """
        if isinstance(data, basestring):
            # Input appears to be JSON. Round trip to validate.
            data_obj = cls._json_to_obj(data)
            return cls._obj_to_json(data_obj)
        else:
            # Assume input is a python structure. Convert to JSON.
            return cls._obj_to_json(data)

    @classmethod
    def _any_to_obj(cls, data):
        """Accept either a JSON or a python structure and
        return a python structure
        """
        if isinstance(data, basestring):
            # Input appears to be JSON. Convert to python structure.
            return cls._json_to_obj(data)
        else:
            # Input appears to be a python stucture.
            # Round trip to validate.
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
        # Override if needed in child
        pass

    def _save_many_to_many_related_objects(self):
        # Cannot create many-to-many relations until both models are
        # saved, but saving the model before defining other fields can raise
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
        if not hasattr(self, key):
            raise AttributeDoesNotExist("Attempted to set attribute %s on class %s, but the attribute does not exist." % (key, self.__class__))
        setattr(self, key, value)

    def _create_or_update_foreign_key_field(self, key, value):
        if value is None:
            setattr(self, key, None)
            return
        else:
            child = self._create_or_update_child(key, value)
            setattr(self, key, child)

    def _create_or_update_many_to_many_field(self, key, valuelist):
        # Cannot create many-to-many relation until model is
        # saved, so we keep a list to save later.
        unsaved_for_this_key = self.unsaved_many_to_many_related_objects.setdefault(key, [])

        if valuelist == [] or valuelist == None:
            # This will remove all many_to_many relations for this field.
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
                raise Error("All model classes must extend ImmutableModel or MutableModel. Neither class found for %s." % child)
        return child

    def _verify_field_is_not_a_parent(self, key):
        if self._is_field_a_parent(key):
            raise ParentNestedInChildException("Setting field %s on class %s is not permitted because the field is a parent. "
                                               "If this field is a foreign key child, add FOREIGN_KEY_CHILDREN = ['%s'] to the class definition of %s" 
                                               % (key, type(self), key, type(self)))

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
                # Child related by reverse Foreign Key (key belongs to the child)
                Model = field.related_model
                self._check_foreign_key_compatibility(Model)
            else:
                raise Error("Unable to find where the related model for field %s is defined." % field)
        if Model._is_abstract(child_value):
            # If child model is abstract or is missing fields,
            # look for a subclass of the child that matches child_value
            child_fields = child_value.keys()
            Model = Model._select_best_subclass_model_by_fields(child_fields)
        self._check_child_compatibility(Model)
        return Model

    def _check_child_compatibility(self, Child):
        """Error if Child is not compatible with parent model (self)
        This is overridden in ImmutableModel
        """
        pass

    def _check_foreign_key_compatibility(self, Child):
        """Error if Child cannot have foreign key to parent
        This is overridden in ImmutableModel
        """
        pass

    @classmethod
    def _is_abstract(cls, data_obj):
        """Detect if the class has subclass, either through abstract inheritance or 
        multitable inheritance.
        _do_all_fields_match will be true for multitable base classes if data_obj 
        contains fields not defined in the base class.
        This method fails to identify a subclass as abstract if it uses multitable inheritance
        but the child adds no new fields, or if the object uses only fields that exist in the 
        parent and none that are unique to the child. Those cases are unsupported.
        """
        return cls._meta.abstract or not cls._do_all_fields_match(data_obj)

    @classmethod
    def _select_best_subclass_model_by_fields(AbstractModel, fields):
        """Find a model that extends AbstractModel and matches the
        fields found in the data object.
        If more than one match are found, rase an exception.
        This works for either an abstract base class or a multitable base class.
        """
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
            # Successfully found one match
            return matching_models[0]
                
    @classmethod
    def _do_all_fields_match(cls, fields):
        """Returns true if all candidate fields are found on this model
        """
        return set(fields).issubset(set(cls._meta.get_all_field_names()))
        
    def downcast(self):
        """ Return the most derived class of this model with the same ID as self.
        If no derived instances exist, return self.
        """
        derived_models = []
        for field in self._get_derived_class_field_names_in_models_with_multitable_inheritance():
            try:
                model = getattr(self, field.name)
                if model._id == self._id:
                    derived_models.append(model)
            except ObjectDoesNotExist:
                # The base class model doesn't have a corresponding derived class instance in this field.
                # Keep looking elsewhere.
                pass
        if len(derived_models) == 0:
            # There are no instances of this model in derived classes. It is already downcast as far as possible.
            # Break out of recursive downcast.
            return self
        elif len(derived_models) > 1:
            raise Error("%s subclasses instances exist for abstract model %s. There should only be one." % (len(submodels), self))
        else:
            # Proceed recursively until no more downcasting is possible.
            return derived_models[0].downcast()

    def _get_derived_class_field_names_in_models_with_multitable_inheritance(self):
        """If you define a BaseModel and extend it with DerivedModel(BaseModel) 
        using multitable inheritance (see below), one of the fields
        on a base BaseModel instance is derivedmodel, and its value is the DerivedModel class.
        This function returns the name of any fields that represent derived model classes.
        This does not apply to abstract inheritance, since you cannot instantiate an instance
        of the abstract base class.

        Abstract inheritance is declared explicitly in the class definition:

        class DerivedModel(BaseModel):
            class Meta:
                abstract=True

        Otherwise the ORM uses multitable inheritance, which means the BaseClass creates its own table, 
        and the  DerivedClass uses a foreignkey to point to its corresponding BaseClass record.

        Multitable inheritance is useful if you need to instantiate the model as a base class.
        """
        derived_model_fields = []
        for field in self._meta.get_fields():
            if isinstance(field, models.fields.related.OneToOneRel) and \
                    issubclass(field.related_model, self.__class__):
                derived_model_fields.append(field)
        return derived_model_fields

    def get_field_as_obj(self, field):
        """Similar function as "to_obj", but this returns only the structure
        stored under "field". 
        This is used recursively with to_obj to render a full model as a python structure.
        """
        if self._does_field_point_to_parent_or_base_class(field):
            # Skip. Ignore these fields in the representation of the model as an obj or json
            return None
        elif isinstance(field, models.fields.related.ManyToManyField):
            return self._get_many_to_many_field_as_obj(field)
        elif isinstance(field, models.fields.related.ForeignKey):
            # If this points to a parent it will return None.
            return self._get_foreign_key_field_as_obj(field)
        elif isinstance(field, models.fields.related.ManyToOneRel):
            return self._get_many_to_one_field_as_obj(field)
        else:
            return helpers.NonserializableTypeConverter.convert_struct(getattr(self, field.name))

    def _does_field_point_to_parent_or_base_class(self, field):
        """This function is used to distinguish fields with no data
        content so they can be ignored.
        """
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
                # The model this key points to is designated as a child.
                # So data in that model is also considered content of self.
                return False
            else:
                # This is a parent model, so its content does not belong to self.
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
        """A field is a Foreign Key Child if designated in the
        model definition with the FOREIGN_KEY_CHILDREN list.
        This is used to flag cases where the model with the pointer
        is considered the child, so its content is contained by the parent
        but not vice versa.
        """
        if hasattr(self, 'FOREIGN_KEY_CHILDREN'):
            return field_name in self.FOREIGN_KEY_CHILDREN
        else:
            return False

    def _get_foreign_key_field_as_obj(self, field):
        """Return the contents of a model linked by a foreign-key field.
        This is called on all foreign keys, so we have to ignore
        the ones where the key points to a parent, since in that case
        # the content does not belong to this model.
        """
        if not self._is_field_a_foreign_key_child(field.name):
            return None

        related_model = getattr(self, field.name)
        if related_model == None:
            return None
        else:
            return related_model.to_obj()

    def _get_many_to_one_field_as_obj(self, field):
        """Return the contents of a model linked by a many-to-one field.
        This is called on all many-to-one relationships, so we have 
        to ignore where the relationship points to a parent, since in 
        that case the content does not belong to this model.
        """
        if not self._is_field_a_foreign_key_child(field.name):
            return None

        related_models = getattr(self, field.name).all()
        return [model.to_obj() for model in related_models]

    def _get_many_to_many_field_as_obj(self, field):
        """Return the contents of models related by a many-to-many field.
        Many-to-many fields must always be defined on the parent, never
        on the child, so all the models we find are children and we return
        all their data.
        """
        related_model_list = getattr(self, field.name)
        related_model_obj = []
        for model in related_model_list.iterator():
            related_model_obj.append(model.to_obj())
        return related_model_obj

    def validate_model(self):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
        pass

    class Meta:
        abstract = True

class MutableModel(_BaseModel):

    """Mutable models use a UUID as their primary key, making their _id value globally unique.
    They can be updated after creation, in contrast to ImmutableModels where the primary key is
    a hash of the contents."""
    
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime_created = models.DateTimeField(default=now)
    datetime_updated = models.DateTimeField(default=now)

    @classmethod
    def create(cls, data_obj_or_json):
        """Use a JSON or python structure to create a model and save 
        it to the database"""
        data_obj = cls._any_to_obj(data_obj_or_json)
        cls.validate_create_input(data_obj)
        # If inheritance is used, create the model instance using the
        # most derived class that matches the fields in the input.
        Model = cls._select_best_subclass_model_by_fields(data_obj)
        # Use a transaction for creation of the model and any children
        with transaction.atomic():
            o = Model()
            o._create_or_update_fields(data_obj)
            o.validate_model()
        return o

    def update(self, update_json):
        """Use a JSON or python structure to update an existing model and
        save it to the database.
        """
        update_obj = self._any_to_obj(update_json)
        self._verify_update_id_matches_model(update_obj.get('_id'))
        # Start with existing model as a dict and update any fields that
        # are contained in update_json
        self.validate_patch_input(update_obj)
        model_obj = self.to_obj()
        model_obj.update(update_obj)
        # Use a transaction for update of the model and any children
        with transaction.atomic():
            self._create_or_update_fields(model_obj)
            self.validate_model()
        return self

    @classmethod
    def validate_create_input(cls, data_obj):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
        pass

    def validate_patch_input(self, data_obj):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
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

    _id = models.CharField(primary_key=True, max_length=255)

    @classmethod
    def create(cls, data_obj_or_json):
        """Use a JSON or python structure to create a model and save 
        it to the database"""
        data_obj = cls._any_to_obj(data_obj_or_json)
        cls.validate_create_input(data_obj)
        _id = cls._verify_input_id_matches_hash(data_obj)
        data_obj.update({'_id': _id})
        # If inheritance is used, create the model instance using the
        # most derived class that matches the fields in the input.
        Model = cls._select_best_subclass_model_by_fields(data_obj)
        # Use a transaction for creation of the model and any children
        with transaction.atomic():
            o = Model()
            o._create_or_update_fields(data_obj)
            o.validate_model()
        return o
            
    @classmethod
    def validate_create_input(cls, data_obj):
        """This can be overridden in the model definitions to include a
        validation routine for that specific model.
        """
        pass

    @classmethod
    def _verify_input_id_matches_hash(cls, data_obj):
        id_from_input = data_obj.get('_id')
        _id = cls._calculate_unique_id(data_obj)
        if id_from_input is not None:
            if id_from_input != _id:
                raise UniqueIdMismatchError(
                    "The input _id %s is out of sync with the hash of contents %s on model %s"
                    %(id_from_input, data_obj, cls.__name__))
        return _id


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
        """Verify that all children are also Immutable. Since Immutable models are a hash
        of their contents, none of their contents, including the contents of their children, 
        can change.
        """
        if not issubclass(Child, ImmutableModel):
            raise MutableChildError("An ImmutableModel can only contain references to ImmutableModels. A %s cannot contain a %s." % (type(self), Child))

    def _check_foreign_key_compatibility(self, Child):
        """Since immutable models are a hash of their content, the same model can arise twice from
        different sources and be the same object in the database. For that reason, there are no
        one-to-many or many-to-one models, only many-to-many.
        This method is called by the base class.
        """
        raise ImmutableChildWithForeignKeyException(
            'Foreign key found on model %s. Foreign keys cannot be used on Immutable models.'
            % Child)

    def to_obj(self):
        """Override base model to include an ID verification.
        """
        obj = super(ImmutableModel, self).to_obj()
        self._verify_unique_id(obj)
        return obj

    def _verify_unique_id(self, obj):
        """Verify that model contents match the model ID, which is a hash of the contents.
        """
        if not self._calculate_unique_id(obj) == self._id:
            raise UniqueIdMismatchError("The _id %s is out of sync with the hash of contents %s on model %s" %(self._id, obj, self.__class__))

    class Meta:
        abstract = True
