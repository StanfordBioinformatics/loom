import copy
import django
from django.db import models
import hashlib
import json
import jsonschema


class InvalidJsonError(Exception):
    pass

class ConvertToJsonError(Exception):
    pass

class ConvertToDictError(Exception):
    pass

class MissingValidationSchemaError(Exception):
    pass

class ModelValidationError(Exception):
    pass

class InvalidValidationSchemaError(Exception):
    pass

class ModelNotFoundError(Exception):
    pass

class IdMismatchError(Exception):
    pass

class NoSaveAllowedError(Exception):
    pass

class AttributeDoesNotExist(Exception):
    pass

class MutableChildError(Exception):
    pass

class CouldNotFindSubclassError(Exception):
    pass

class CouldNotFindUniqueSubclassError(Exception):
    pass

class ForeignKeyInChildError(Exception):
    pass

class _BaseModel(models.Model):

    def to_json(self):
        obj = self.to_obj()
        return self._obj_to_json(obj)

    def to_obj(self):
        obj = self._get_fields_as_obj()
        obj.update(self._get_many_to_many_fields_as_obj())
        return obj

    @classmethod
    def get_by_id(cls, _id):
        return cls.objects.get(_id=_id)

    @classmethod
    def _obj_to_json(cls, data_obj):
        JSON_DUMP_OPTIONS = {'separators': (',',':'), 'sort_keys': True}
        try:
            return json.dumps(data_obj, **JSON_DUMP_OPTIONS)
        except Exception as e:
            raise ConvertToJsonError('Could not convert object to JSON. "%s". %s' % (data_obj, e.message))

    @classmethod
    def _json_to_obj(cls, data_json):
        try:
            data_obj =json.loads(data_json)
        except Exception as e:
            raise InvalidJsonError('Invalid JSON. "%s". %s' % (data_json, e.message))
        return data_obj

    @classmethod
    def _any_to_json(cls, data_obj_or_json):
        if isinstance(data, basestring):
            # Round trip to validate JSON and standardize format
            data_obj = cls._json_to_obj(data_obj_or_json)
        else:
            data_obj = data_obj_or_json(data)
        return cls._obj_to_json(data_obj)

    @classmethod
    def _any_to_obj(cls, data):
        if isinstance(data, basestring):
            data_json = data
        else:
            # Round trip to validate
            data_json = cls._obj_to_json(data)
        return cls._json_to_obj(data_json)

    def _create_or_update_attributes(self, data_obj):
        self.unsaved_many_to_many = {}
        for (key, value) in data_obj.iteritems():
            self._create_or_update_attribute(key, value)
        self._process_many_to_many_relations()

    def _process_many_to_many_relations(self):
        # Cannot create many-to-many relation until model is
        # saved, but saving before adding other fields will raise
        # errors if those fields are required (null=False).
        # Now that all other fields are added, we save once,
        # then add many-to-many relations, then save again.
        models.Model.save(self)
        while self.unsaved_many_to_many:
            (key, children) = self.unsaved_many_to_many.popitem()
            field = getattr(self, key)
            field.clear()
            for child in children:
                field.add(child)
        models.Model.save(self)

    def _create_or_update_attribute(self, key, value):
        if isinstance(value, list):
            self._create_or_update_many_to_many_attribute(key, value)
        elif isinstance(value, dict):
            self._create_or_update_foreign_key_attribute(key, value)
        else:
            self._create_or_update_scalar_attribute(key, value)

    def _create_or_update_scalar_attribute(self, key, value):
        if not hasattr(self, key):
            raise AttributeDoesNotExist("Attempted to set attribute %s on class %s, but the attribute does not exist." % (key, self.__class__))
        setattr(self, key, value)

    def _create_or_update_foreign_key_attribute(self, key, value):
        if value is None:
            setattr(self, key, None)
            return
        else:
            Model = self._get_model_for_attribute_name(key, value)
            if value.get('id') is not None:
                child = Model.objects.get(id=value.get('id'))
                child.update(value)
            else:
                child = Model.create(value)
            setattr(self, key, child)

    def _create_or_update_many_to_many_attribute(self, key, valuelist):
        # Cannot create many-to-many relation until model is
        # saved, so we keep a list to save later.
        unsaved_for_this_key = self.unsaved_many_to_many.setdefault(key, [])

        if valuelist == [] or valuelist == None:
            return
        else:
            for value in valuelist:
                Model = self._get_model_for_attribute_name(key, value)
                if value.get('id') is not None:
                    child = Model.objects.get(id=value.get('id'))
                    child.update(value)
                else:
                    child = Model.create(value)
                unsaved_for_this_key.append(child)

    def _get_model_for_attribute_name(self, key, value):
        field = self._meta.get_field(key)
        try:
            Model = field.related.model
        except AttributeError as e:
            if isinstance(field, django.db.models.ManyToOneRel):
                raise ForeignKeyInChildError('Foreign keys from child to parent are not supported.')
            else:
                raise e
        if Model._is_abstract(value):
            Model = Model._select_best_subclass_model(value)
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
    def _select_best_subclass_model(AbstractModel, data_obj):
        # This works for either abstract base class or multitable base class
        subclass_models = []
        for Model in django.apps.apps.get_models():
            if issubclass(Model, AbstractModel):
                subclass_models.append(Model)
        matching_models = []
        for Model in subclass_models:
            if Model._do_all_fields_match(data_obj):
                matching_models.append(Model)
        if len(matching_models) == 0:
            raise CouldNotFindSubclassError("Failed to find a subclass of abstract model %s that matches these fields: %s" % (AbstractModel, data_obj))
        elif len(matching_models) > 1:
            raise CouldNotFindUniqueSubclassError(
                "Failed to find a unique subclass of abstract model %s that matches these fields: %s. Multiple models matched: %s" 
                % (AbstractModel, data_obj, matching_models))
        else:
            return matching_models[0]
                
    @classmethod
    def _do_all_fields_match(cls, data_obj):
        model_fields = cls._meta.get_all_field_names()
        data_fields = data_obj.keys()
        for field in data_fields:
            if field not in model_fields:
                return False
        return True
        
    def _get_fields_as_obj(self):
        obj = {}
        for field in self._meta.fields:
            obj[field.name] = self._get_field_as_obj(field)
        return obj

    def _get_field_as_obj(self, field):
        if isinstance(field, models.fields.related.ForeignKey):
            return self._get_foreign_key_field_as_obj(field)
        else:
            return getattr(self, field.name)

    def _get_foreign_key_field_as_obj(self, field):
        related_model = getattr(self, field.name)
        if related_model == None:
            return None
        else:
            return related_model.to_obj()

    def _get_many_to_many_fields_as_obj(self):
        obj = {}
        for field in self._meta.many_to_many:
            obj[field.name] = self._get_many_to_many_field_as_obj(field)
        return obj

    def _get_many_to_many_field_as_obj(self, field):
        related_model_list = getattr(self, field.name)
        related_model_obj = []
        for model in related_model_list.iterator():
            related_model_obj.append(model.to_obj())
        return related_model_obj

    class Meta:
        abstract = True

class MutableModel(_BaseModel):

    _id = models.AutoField(primary_key=True)

    @classmethod
    def create(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        Model = cls._select_best_subclass_model(data_obj)
        o = Model()
        o._create_or_update_attributes(data_obj)
        return o

    def update(self, data_json):
        data_obj = self._any_to_obj(data_json)
        self._verify_id(data_obj.get('_id'))
        model_obj = self.to_obj()
        model_obj.update(data_obj)
        model_json = self._obj_to_json(model_obj)
        self._create_or_update_attributes(data_obj)
        return self

    def _verify_id(self, _id):
        if _id is None:
            return
        if _id != self._id:
            raise IdMismatchError('ID mismatch. The update JSON gave an id of "%s", but this model has id "%s"'
                            % (_id, self._id))

    class Meta:
        abstract = True

class ImmutableModel(_BaseModel):

    _id = models.TextField(primary_key=True, null=False)

    @classmethod
    def create(cls, data_obj_or_json):
        data_obj = cls._any_to_obj(data_obj_or_json)
        data_json = cls._obj_to_json(data_obj)
        _id = cls._calculate_unique_id(data_json)
        data_obj.update({'_id': _id})
        Model = cls._select_best_subclass_model(data_obj)
        o = Model()
        o._create_or_update_attributes(data_obj)
        return o

    def save(self):
        raise NoSaveAllowedError("Immutable models cannot be saved after creation.")

    @classmethod
    def _calculate_unique_id(cls, data_json):
        return hashlib.sha256(data_json).hexdigest()

    def _check_child_compatibility(self, Child):
        if not issubclass(Child, ImmutableModel):
            raise MutableChildError("An ImmutableModel can only contain references to ImmutableModels.")

    class Meta:
        abstract = True
