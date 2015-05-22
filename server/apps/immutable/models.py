import copy
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

class IdMismatchException(Exception):
    pass

class _BaseModel(models.Model):

    @classmethod
    def _sanitize_input(cls, data_json):
        data_json = cls._any_to_json(data_json)
        data_obj = cls._json_to_obj(data_json)
        cls._validate_schema(data_obj)
        return data_obj

    @classmethod
    def _obj_to_json(cls, data_obj):
        JSON_DUMP_OPTIONS = {'separators': (',',':'), 'sort_keys': True}
        return json.dumps(data_obj, **JSON_DUMP_OPTIONS)

    @classmethod
    def _json_to_obj(cls, data_json):
        try:
            data_obj =json.loads(data_json)
        except ValueError as m:
            raise InvalidJsonError('Invalid JSON. "%s". %s' % (data_json, m.message))
        return data_obj

    @classmethod
    def _any_to_json(cls, data):
        if isinstance(data, dict):
            return cls._obj_to_json(data)
        elif isinstance(data, basestring):
            return data
        else:
            raise ConvertToJsonError("Failed to convert this to JSON: %s" % data)

    @classmethod
    def _any_to_obj(cls, data):
        if isinstance(data, dict):
            return data
        elif isinstance(data, basestring):
            return cls._json_to_obj(data)
        else:
            raise ConvertToDictError('Invalid type for converting to a dict: "%s". Expected a dict or a JSON string.' % data)

    @classmethod
    def _validate_schema(cls, data_obj):
        if not hasattr(cls, 'validation_schema'):
            raise MissingValidationSchemaError("Validation failed because the 'validation_schema' attribute is not defined for the class %s" % self.__class__.__name__)
        schema = cls._get_validation_schema()
        try:
            jsonschema.validate(data_obj, schema)
        except jsonschema.SchemaError as e:
            raise ModelValidationError('Model validation failed with error "%s". Model: "%s". Schema: "%s".' % (e.message, data_obj, schema))
        except AttributeError as e:
            raise InvalidValidationSchemaError('Invalid model validation schema: "%s"' % schema)

    @classmethod
    def _get_validation_schema(cls):
        schema = copy.deepcopy(cls.validation_schema)
        if not hasattr(cls, '_extra_validation_schema_fields'):
            return schema
        properties = schema.get('properties')
        if properties is None:
            return # Invalid schema. Will raise error when calling validate.
        properties.update(cls._extra_validation_schema_fields)
        return schema

    def _create_or_update_attributes(self, data_obj):
        self.unsaved_many_to_many = {}
        for (key, value) in data_obj.iteritems():
            self._create_or_update_attribute(key, value)
        self._process_many_to_many_relations()

    def _process_many_to_many_relations(self):
        # Cannot create many-to-many relation until model is
        # saved, but saving before adding other fields will raise
        # errors if those fields are required.
        # Now that all other fields are added, we save once,
        # then add many to many relations, then save again.
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
            raise Exception("Attempted to set attribute %s on class %s, but the attribute does not exist." % (key, self.__class__))
        setattr(self, key, value)

    def _create_or_update_foreign_key_attribute(self, key, value):
        if value is None:
            setattr(self, key, None)
            return
        else:
            Model = self._get_model_for_attribute_name(key)
            if value.get('id') is not None:
                child = Model.objects.get(id=value.get('id'))
                child.update(value)
            else:
                child = Model.create(value)
            setattr(self, key, child)

    def _create_or_update_many_to_many_attribute(self, key, valuelist):
        Model = self._get_model_for_attribute_name(key)
        if valuelist == [] or valuelist == None:
            return
        else:
            for value in valuelist:
                if value.get('id') is not None:
                    child = Model.objects.get(id=value.get('id'))
                    child.update(value)
                else:
                    child = Model.create(value)
                # Cannot create many-to-many relation until model is
                # saved, so we keep a list to save later.
                unsaved_for_this_key = self.unsaved_many_to_many.setdefault(key, [])
                unsaved_for_this_key.append(child)

    def _get_model_for_attribute_name(self, key):
        field = self._meta.get_field(key)
        return field.related.model

    def to_json(self):
        obj = self.to_obj()
        return self._obj_to_json(obj)

    def to_obj(self):
        obj = self._get_fields_as_obj()
        obj.update(self._get_many_to_many_fields_as_obj())
        return obj

    def _get_fields_as_obj(self):
        obj = {}
        EXCLUDED_FIELDS = ['_basemodel_ptr', 'mutablemodel_ptr']
        for field in self._meta.fields:
            if field.name in EXCLUDED_FIELDS:
                continue
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

    @classmethod
    def get_by_id(cls, _id):
        return cls.objects.get(_id=_id)

    class Meta:
        abstract = True

class MutableModel(_BaseModel):

    _id = models.AutoField(primary_key=True)
    _extra_validation_schema_fields = {'_id': {'type': 'integer'}}

    @classmethod
    def create(cls, dirty_data_json):
        data_obj = cls._sanitize_input(dirty_data_json)
        o = cls()
        o._create_or_update_attributes(data_obj)
        return o

    def update(self, data_json):
        data_obj = self._any_to_obj(data_json)
        self._verify_id(data_obj.get('_id'))
        dirty_model_obj = self.to_obj()
        dirty_model_obj.update(data_obj)
        model_obj = self._sanitize_input(dirty_model_obj)
        model_json = self._obj_to_json(model_obj)
        self._create_or_update_attributes(data_obj)
        return self

    def _verify_id(self, _id):
        if _id is None:
            return
        if _id != self._id:
            raise IdMismatchException('ID mismatch. The update JSON gave an id of "%s", but this model has id "%s"'
                            % (_id, self._id))

class ImmutableModel(_BaseModel):

    _id = models.TextField(primary_key=True, blank=False, null=False)

    @classmethod
    def create(cls, dirty_data_json):
        data_json = cls._any_to_json(dirty_data_json)
        _id = cls._calculate_unique_id(data_json)
        data_obj = cls._json_to_obj(data_json)
        data_obj.update({
            '_id': _id
        })
        o = cls.create(data_obj)
        return o

    @classmethod
    def create(cls, dirty_data_json):
        data_obj = cls._sanitize_input(dirty_data_json)
        data_json = cls._obj_to_json(data_obj)
        o = cls()
        o._id = o._calculate_unique_id(data_json)
        o._create_or_update_attributes(data_obj)
        return o

    @classmethod
    def _calculate_unique_id(cls, data_json):
        return hashlib.sha256(data_json).hexdigest()

    def save(self):
        raise Exception("Immutable models cannot be saved after creation.")


class SampleMutableChild(MutableModel):
    name = models.CharField(max_length=100)
    validation_schema = {'type': 'object',
                         'properties': {
                             'name': {
                                 'type': 'string',
                             }
                         },
                         'additionalProperties': False
    }

class SampleMutableChild2(MutableModel):
    name = models.CharField(max_length=100)
    validation_schema = {'type': 'object',
                         'properties': {
                             'name': {
                                 'type': 'string',
                             }
                         },
                         'additionalProperties': False
    }


class SampleMutableParent(MutableModel):
    name = models.CharField(max_length=100)
    listofchildren = models.ManyToManyField(SampleMutableChild2)
    singlechild = models.ForeignKey(SampleMutableChild, null=True)
    validation_schema = {'type': 'object',
                         'properties': {
                             'name': {
                                 'type': 'string'
                             },
                             'singlechild': {
                                 'type': ['object', 'null']
                             },
                             'listofchildren': {
                                 'type': 'array',
                                 'items': {
                                     'type': ['object', 'null']
                                 }
                             }
                         },
                         'additionalProperties': False
    }

class SampleImmutableParent(ImmutableModel):
    name = models.CharField(max_length=100)
    validation_schema = {'type': 'object',
                         'properties': {
                             'name': {
                                 'type': 'string',
                             }
                         },
                         'additionalProperties': False
    }


class SampleImmutableChild(ImmutableModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(SampleImmutableParent, related_name='child')
    validation_schema = {'type': 'object',
                         'properties': {
                             'name': {
                                 'type': 'string',
                             },
                             'parent': {
                                 'type': 'object'
                             }
                         },
                         'additionalProperties': False
    }
