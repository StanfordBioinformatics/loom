import json
import numbers
import re

from django.db import models
from django.core.exceptions import ValidationError


class _BaseModel(models.Model):

    metadata = models.TextField(blank=True, null=True, validators=['_validate_json'])

    @classmethod
    def _validate_keys(cls, data_struct, required=None, optional=None):
        for key in data_struct.keys():
            if key not in required and key not in optional:
                raise ValidationError('%s is not a valid field. required fields: %s, optional fields: %s' % (key, required, optional))
        if required is not None:
            for key in required:
                if key not in data_struct.keys():
                    raise ValidationError('Required field %s is missing' % key)

    @classmethod
    def _validate_values(cls, data_struct, allowed_values_dict):
        for key, allowed_values in allowed_values_dict.iteritems():
            if key in data_struct.keys():
                value = data_struct[key]
                if value not in allowed_values:
                    raise ValidationError('%s is not a valid value for %s. Accepted values: %s' % (value, key, allowed_values))

    @classmethod
    def _validate_json(cls, raw_data):
        try:
            data_struct = json.loads(raw_data)
        except ValueError:
            raise ValidationError("Can't initialize object from an invalid JSON. data=%s" % data)
        return data_struct

    @classmethod
    def _validate_object_class(cls, value, required_class):
        if value is None:
            return
        try:
            # If required_class is a list
            match = False
            for each_class in required_class:
                match = match or isinstance(value, each_class)
            if not match:
                raise ValidationError('%s is not a valid object of classes %s' % (value, required_class))
        except TypeError:
            # If required_class is scalar
            if not isinstance(value, required_class):
                raise ValidationError('%s is not a valid object of class %s' % (value, required_class))

    @classmethod
    def _strip_metadata_from_struct(cls, data_struct):
        try:
            metadata = data_struct.pop('metadata')
        except KeyError:
            metadata = None
        return metadata

class _DataTypeValidator:
    # A mixin for models that need to parse and validate DataObject types

    SCALAR_TYPES = ['boolean', 'file', 'float', 'integer', 'string']
    NONSCALAR_TYPES = {
        'array': {'re': r'array\[(.*)\]'},
        'tuple': {'re': r'tuple\[(.*)\]'},
        }              

    @classmethod
    def _validate_data_type(cls, type, value = None):
        type_validator = {
            'array': cls._validate_array,
            'boolean': cls._validate_boolean,
            'file': cls._validate_file,
            'float': cls._validate_float,
            'integer': cls._validate_integer,
            'string': cls._validate_string,
            'tuple': cls._validate_tuple,
            }

        if type in cls.SCALAR_TYPES:
            type_validator[type](value)

        # Nonscalar types will recursively call this method to validate the types of their members
        elif re.match(cls.NONSCALAR_TYPES['array']['re'], type):
            type_validator['array'](type, value)
        elif re.match(cls.NONSCALAR_TYPES['tuple']['re'], type):
            type_validator['tuple'](type, value)

        else:
            raise ValidationError('%s is not a valid type.' % type)

    @classmethod
    def _validate_boolean(cls, value):
        cls._validate_object_class(value, bool)

    @classmethod
    def _validate_file(cls, value):
        VALID_HASH_ALGORITHMS = ['sha-256']
        cls._validate_keys(value, required=['hash_algorithm', 'hash_value'])
        cls._validate_values(value, {'hash_algorithm': VALID_HASH_ALGORITHMS})
        cls._validate_object_class(value['hash_value'], [str, unicode])

    @classmethod
    def _validate_float(cls, value):
        cls._validate_object_class(value, float)
        
    @classmethod
    def _validate_integer(cls, value):
        cls._validate_object_class(value, numbers.Integral)

    @classmethod
    def _validate_string(cls, value):
        cls._validate_object_class(value, [str, unicode])

    @classmethod
    def _validate_array(cls, array_type, array_value):
        # Get the type of the array members,
        # e.g. array[tuple[boolean, string]]
        # -> tuple[boolean, string]
        m = re.match(cls.NONSCALAR_TYPES['array']['re'], array_type)
        member_type = m.groups()[0]
        if array_value is not None:
            cls._validate_object_class(array_value, list)
            for member_value in array_value:
                cls._validate_data_type(member_type, member_value)

    @classmethod
    def _validate_tuple(cls, tuple_type, tuple_value):
        # Get the type of the tuple members,
        # e.g. tuple[boolean, string, tuple[file, file]]
        # -> boolean, string, tuple[file, file]
        m = re.match(cls.NONSCALAR_TYPES['tuple']['re'], tuple_type)
        member_type_string = m.groups()[0]

        # Split on commas not in parentheses
        # e.g. 'boolean, string, tuple[file, file]'
        # -> ['boolean', 'string', 'tuple[file, file]']
        member_type_list = []
        parentheses_counter = 0
        last_split = 0
        for i in range(len(member_type_string)):
            letter = member_type_string[i]
            if letter == '[':
                parantheses_counter += 1
            elif letter == ']':
                parantheses_counter -= 1
            elif letter == ',' and parentheses_counter == 0:
                member_type_list.append(member_type_string[last_split:i].strip())
                last_split = i+1
        member_type_list.append(member_type_string[last_split:].strip())

        if parentheses_counter != 0:
            raise ValidationError('Unbalanced expression: %s' % tuple_type)

        if tuple_value is not None:
            cls._validate_object_class(tuple_value, list)
            if len(tuple_value) != len(member_type_list):
                raise ValidationError('List of tuple types did not match length of tuple values. Types: %s; Values: %s' % (tuple_type, tuple_value))

            for i in range(len(tuple_value)):
                cls._validate_data_type(member_type_list[i], tuple_value[i])


class _AbstractAnalysis(_BaseModel):

    ports = models.ManyToManyField('Port')


class Container(_BaseModel):

    hash_algorithm = models.CharField(max_length=20)
    hash_value = models.TextField()
    VALID_HASH_ALGORITHMS = ['sha-256']

    @classmethod
    def create(cls, raw_data):
        data_struct = cls._validate_json(raw_data)
        cls._validate_keys(data_struct, required=['hash_algorithm', 'hash_value'], optional=['metadata'])
        cls._validate_object_class(data_struct['hash_algorithm'], [str, unicode])
        cls._validate_object_class(data_struct['hash_value'], [str, unicode])
        cls._validate_values(data_struct, {'hash_algorithm': cls.VALID_HASH_ALGORITHMS})
        metadata = data_struct._strip_metadata_from_struct()
        o = Container(
            hash_algorithm=data_struct['hash_algorithm'],
            hash_value=data_struct['hash_value'],
            metadata=metadata,
            )
        o.save()


class Environment(_BaseModel):
    containers = models.ManyToManyField(Container)

    @classmethod
    def create(cls, raw_data):
        data_struct = self._validate_json(raw_data)
        self._validate_keys(data_struct, required=['containers'], optional=['metadata'])
        metadata = data_struct._strip_metadata_from_struct()
        o = Environment(metadata=metadata)
        for container in data_struct['containers']:
            # TODO
            container_object = None
            #container_object = Containers.object.get(pk=container.id)
            if not container_object:
                container_object.create(json.dumps(container))
            o.containers.add(container_object)
        o.save()

class Task(_AbstractAnalysis):

    VALID_INTERPRETERS = ['python', 'bash']
    interpreter = models.CharField(max_length=20)
    script = models.TextField()
    environment = models.ForeignKey(Environment)


class Analysis(_AbstractAnalysis):
    # ports
#    child_analyses = models.ManyToManyField(_AbstractAnalysis)
    # bindings
    # childbindings

    class Meta:
        verbose_name_plural = "analyses"


class _AbstractDataObject(_BaseModel, _DataTypeValidator):
    pass


class DataImport(_AbstractDataObject):
    import_note = models.TextField()


class DataObject(_AbstractDataObject):

    # data is in JSON format
    data = models.TextField()
#    source = models.ForeignKey(_AbstractDataObject)

    def to_json(self, metadata=True):
        data = json.loads(self.data)
        if metadata:
            data['metadata'] = self.metadata
        return json.dumps(data)

    @classmethod
    def create(cls, raw_data):
        cleaned_data_struct = DataObject._clean(raw_data)
        metadata = cls._strip_metadata_from_struct(cleaned_data_struct)
        o = DataObject(
            data=json.dumps(
                cleaned_data_struct, 
                sort_keys=True
                ),
            metadata=metadata,
            )
        o.save()
        return o

    @classmethod
    def _clean(cls, raw_data):
        data_struct = cls._validate_json(raw_data)
        cls._validate_struct(data_struct)
        return data_struct

    @classmethod
    def _validate_struct(cls, data_struct):
        cls._validate_keys(data_struct, required=['type', 'value'], optional='metadata')
        cls._validate_data_type(data_struct['type'], data_struct['value'])


class Port(_AbstractDataObject):
    name = models.CharField(max_length = 100)
    port_type = models.CharField(max_length = 20)
    data_type = models.TextField()

    PORT_TYPES = ['input', 'output']

    def to_json(self, metadata=True):
        data = {'data_type': self.data_type, 'port_type': self.port_type, 'name': self.name}
        if metadata:
            data['metadata'] = self.metadata
        return json.dumps(data, sort_keys=True)

    @classmethod
    def create(cls, raw_data):
        cleaned_data = Port._clean(raw_data)
        metadata = cls._strip_metadata_from_struct(cleaned_data)
        o = Port(
            metadata=metadata,
            data_type=cleaned_data['data_type'], 
            port_type=cleaned_data['port_type'], 
            name=cleaned_data['name']
            )
        o.save()
        return o

    @classmethod
    def _clean(cls, raw_data):
        data_struct = cls._validate_json(raw_data)
        cls._validate_struct(data_struct)
        return data_struct

    @classmethod
    def _validate_struct(cls, data_struct):
        cls._validate_keys(data_struct, required=['name', 'data_type', 'port_type'], optional=['metadata'])
        cls._validate_values(data_struct, {'port_type': cls.PORT_TYPES})
        cls._validate_data_type(data_struct['data_type'])

class Binding(_BaseModel):

#    source = models.ForeignKey(_AbstractDataObject)
#    destination = models.ForeignKey(_AbstractDataObject)
#    parent_analysis = models.ForeignKey(Analysis)

    @classmethod
    def create(cls, raw_data):
        #TODO
        pass

    def to_json(self, metadata=True):
        pass

class ChildBinding(_BaseModel):

#    source = models.ForeignKey(Port)
#    destination = models.ForeignKey(Port)

    @classmethod
    def create(cls, raw_data):
        #TODO
        pass

    def to_json(self, metadata=True):
        pass
