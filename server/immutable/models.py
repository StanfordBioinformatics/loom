import copy
import django
from django.db import models
import hashlib
import json
import jsonschema
import uuid
from immutable import helpers
from immutable.exceptions import *

class _BaseModel(models.Model):

    @classmethod
    def get_by_id(cls, _id):
        return cls.objects.get(_id=_id)

    def get(self, field_name):
        try:
            field_value = getattr(self, field_name)
        except:
            return None
        try:
            return field_value.downcast()
        except:
            return field_value

    def to_json(self):
        obj = self.to_obj()
        return self._obj_to_json(obj)

    def to_obj(self):
        model = self.downcast()
        return model._get_fields_as_obj()

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
        models.Model.save(self)
        self._save_many_to_many_related_objects()

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
        if isinstance(value, list):
            self._create_or_update_many_to_many_field(key, value)
        elif isinstance(value, dict):
            self._create_or_update_foreign_key_field(key, value)
        else:
            self._create_or_update_scalar_field(key, value)

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
                raise ForeignKeyInChildError('Foreign keys from child to parent are not supported.')
            else:
                raise Exception("Unknown exception %s" % e.message)
        if Model._is_abstract(child_value):
            # If child model is abstract or is missing fields, look for a subclass that matches child_value
            child_fields = child_value.keys()
            Model = Model._select_best_subclass_model_by_fields(child_fields)
        self._check_child_compatibility(Model)
        return Model

    def _check_child_compatibility(self, Child):
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
            if (field_obj is None) or (field_obj == []):
                continue
            if isinstance(field_obj, uuid.UUID):
                field_obj = str(field_obj)
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
        elif isinstance(field, models.fields.related.ManyToOneRel) and \
                isinstance(self, field.model):
            # This is a ForeignKey defined on the parent model.
            return True
        else:
            return False

    def _get_foreign_key_field_as_obj(self, field):
        related_model = getattr(self, field.name)
        if related_model == None:
            return None
        else:
            return related_model.to_obj()

    def _get_many_to_many_field_as_obj(self, field):
        related_model_list = getattr(self, field.name)
        related_model_obj = []
        for model in related_model_list.iterator():
            related_model_obj.append(model.to_obj())
        return related_model_obj

    class Meta:
        abstract = True

class MutableModel(_BaseModel):

    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    @classmethod
    def create(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        Model = cls._select_best_subclass_model_by_fields(data_obj)
        o = Model()
        o._create_or_update_fields(data_obj)
        return o

    def update(self, update_json):
        update_obj = self._any_to_obj(update_json)
        self._verify_update_id_matches_model(update_obj.get('_id'))
        # Start with existing model and update any fields in update_json
        model_obj = self.to_obj()
        model_obj.update(update_obj)
        self._create_or_update_fields(model_obj)
        return self

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
        data_json = cls._obj_to_json(data_obj)
        _id = cls._calculate_unique_id(data_json)
        data_obj.update({'_id': _id})
        Model = cls._select_best_subclass_model_by_fields(data_obj)
        o = Model()
        o._create_or_update_fields(data_obj)
        return o

    def save(self):
        raise NoSaveAllowedError("Immutable models cannot be saved after creation.")

    @classmethod
    def _calculate_unique_id(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        return helpers.IdCalculator(data_obj=data_obj, id_key='_id').get_id()

    def _check_child_compatibility(self, Child):
        if not issubclass(Child, ImmutableModel):
            raise MutableChildError("An ImmutableModel can only contain references to ImmutableModels.")

    def to_obj(self):
        obj = super(ImmutableModel, self).to_obj()
        self._verify_unique_id(obj)
        return obj

    def _verify_unique_id(self, obj):
        if not self._calculate_unique_id(obj) == self._id:
            raise UniqueIdMismatchError("The _id %s is out of sync with the hash of contents %s on model %s" %(self._id, obj, self.__class__))

    class Meta:
        abstract = True
