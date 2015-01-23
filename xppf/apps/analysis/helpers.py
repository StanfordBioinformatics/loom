import json
import numbers
import re

from django.core.exceptions import ValidationError

class ValidationHelper:

    @classmethod
    def validate_keys(cls, data_obj, required=None, optional=None):
    
        # Verifies that 'data_obj' contains all keys listed in 'required'
        # Verifies that 'data_obj' does not contain any keys not listed in 'required' or 'optional'

        # None is a valid input but replaced with an empty list
        keys = data_obj.keys()
        if keys is None:
            keys = []
        if required is None:
            required = []
        if optional is None:
            optional = []

        for key in keys:
            if key not in required and key not in optional:
                raise ValidationError('%s is not a valid field. required fields: %s, optional fields: %s' % (key, required, optional))
        if required is not None:
            for key in required:
                if key not in keys:
                    raise ValidationError('Required field %s is missing' % key)

    @classmethod
    def validate_key(cls, data_obj, key, expected_class=None):
        # Verify key is found
        if key not in data_obj:
            raise ValidationError("The key %s was not found. Data object = %s" % (key, data_obj))
        value = data_obj.get(key)
        # Ignore class if none is provided
        if expected_class is not None:
            cls.validate_object_class(value, expected_class)
        return value

    @classmethod
    def validate_in(cls, value, value_list):
        if value not in value_list:
            raise ValidationError("%s was not found in the list of allowed values %s" % (value, value_list))

    @classmethod
    def validate_values(cls, data_obj, allowed_values_dict):
        
        # Verifies that values in 'data_obj'
        # are contained in a list of allowed values 'allowed_values_dict'

        for key, allowed_values in allowed_values_dict.iteritems():
            if key in data_obj.keys():
                value = data_obj[key]
                if value not in allowed_values:
                    raise ValidationError('%s is not a valid value for %s. Accepted values: %s' % (value, key, allowed_values))

    @classmethod
    def validate_and_parse_json(cls, raw_data):

        # Verifies that 'raw_data' is a valid JSON
        # If valid, it returns the corresponding Python object

        try:
            data_obj = json.loads(raw_data)
        except ValueError:
            raise ValidationError("Can't initialize object from an invalid JSON. data=%s" % raw_data)
        return data_obj

    @classmethod
    def validate_object_class(cls, value, required_class):

        # Verifies that 'value' of the class 'required_class'
        # None is always an accepted value.
        # 'required_class' is a string with the name of a class
        # or a list of strings naming all acceptable classes.

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

class DataObjectTypeHelper:

    # For parsing and validating DataObject types
    #
    # In addition to scalar data types, DataObjects may be tuples or arrays.
    # Types may be nested, so the members of tuples or arrays may be scalars, tuples, or arrays.
    # Members of an array must all have identical type, but members of a tuple can differ.
    # Array type is specified as 'array[boolean]' or 'array[array[boolean]]', for example.
    # Tuple type is specified as 'tuple[string, boolean]' or 'tuple[array[string], boolean], for example.


    SCALAR_TYPES = ['boolean', 'file', 'float', 'integer', 'string']
    NONSCALAR_TYPES = {
        'array': {'regex': r'array\[(.*)\]'},
        'tuple': {'regex': r'tuple\[(.*)\]'},
        }

    @classmethod
    def validate_data_type(cls, data_type, value = None):

        # Raise Exception if 'value' is not of the type specified by 'data_type'
        # Nonscalar types like 'array[tuple[string, boolean]]' are handled by recursively 
        # calling this method to validate the  member types

        type_validator = {
            'array': cls.validate_array,
            'boolean': cls.validate_boolean,
            'file': cls.validate_file,
            'float': cls.validate_float,
            'integer': cls.validate_integer,
            'string': cls.validate_string,
            'tuple': cls.validate_tuple,
            }

        if data_type in cls.SCALAR_TYPES:
            type_validator[data_type](value)
        elif re.match(cls.NONSCALAR_TYPES['array']['regex'], data_type):
            type_validator['array'](data_type, value)
        elif re.match(cls.NONSCALAR_TYPES['tuple']['regex'], data_type):
            type_validator['tuple'](data_type, value)
        else:
            raise ValidationError('%s is not a valid type.' % data_type)

    @classmethod
    def validate_boolean(cls, value):
        ValidationHelper.validate_object_class(value, bool)

    @classmethod
    def validate_file(cls, value):
        VALID_HASH_ALGORITHMS = ['sha-256']
        ValidationHelper.validate_keys(value, required=['hash_algorithm', 'hash_value'])
        ValidationHelper.validate_values(value, {'hash_algorithm': VALID_HASH_ALGORITHMS})
        ValidationHelper.validate_object_class(value['hash_value'], [str, unicode])

    @classmethod
    def validate_float(cls, value):
        ValidationHelper.validate_object_class(value, float)
        
    @classmethod
    def validate_integer(cls, value):
        ValidationHelper.validate_object_class(value, numbers.Integral)

    @classmethod
    def validate_string(cls, value):
        ValidationHelper.validate_object_class(value, [str, unicode])

    @classmethod
    def validate_array(cls, array_type, array_value):
        # Get the type of the array members,
        # e.g. array[tuple[boolean, string]]
        # -> tuple[boolean, string]
        m = re.match(cls.NONSCALAR_TYPES['array']['regex'], array_type)
        member_type = m.groups()[0]
        if array_value is not None:
            ValidationHelper.validate_object_class(array_value, list)
            for member_value in array_value:
                cls.validate_data_type(member_type, member_value)

    @classmethod
    def validate_tuple(cls, tuple_type, tuple_value):
        member_type_list = cls._get_tuple_type_members(tuple_type)

        if tuple_value is not None:
            ValidationHelper.validate_object_class(tuple_value, list)
            if len(tuple_value) != len(member_type_list):
                raise ValidationError('List of tuple types did not match length of tuple values. Types: %s; Values: %s' % (tuple_type, tuple_value))

            # Now validate all tuple members
            for i in range(len(tuple_value)):
                cls.validate_data_type(member_type_list[i], tuple_value[i])

    @classmethod
    def _get_tuple_type_members(cls, tuple_type):

        # Get the type of the tuple members,
        # e.g. for tuple_type = 'tuple[boolean, string, tuple[file, file]]',
        # we find member_type_string = 'boolean, string, tuple[file, file]'
        m = re.match(cls.NONSCALAR_TYPES['tuple']['regex'], tuple_type)
        member_type_string = m.groups()[0]

        # Split member_type_string at the top level,
        # only on commas that are not in parentheses.
        # e.g. member_type_string = 'boolean, string, tuple[file, file]'
        # will produce this member_type_list:
        # ['boolean', 'string', 'tuple[file, file]']
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

        return member_type_list
