import copy
import datetime
import hashlib
import json
import uuid

from .exceptions import *


JSON_DUMP_OPTIONS = {'separators': (',',':'), 'sort_keys': True}

def struct_to_json(data_struct):
    try:
        data_struct = NonserializableTypeConverter.convert_struct(data_struct)
        return json.dumps(data_struct, **JSON_DUMP_OPTIONS)
    except Exception as e:
        raise ConvertToJsonError(
            'Could not convert struct to JSON. "%s". %s'
            % (data_struct, e.message))

def json_to_struct(data_json):
    try:
        data_struct =json.loads(data_json)
    except Exception as e:
        raise InvalidJsonError(
            'Invalid JSON. "%s". %s' % (data_json, e.message))
    return data_struct


class StripKey(object):
    """Crawls a python data structure and removes
    any data with the designated key name
    """

    @classmethod
    def strip_key(cls, struct, key):
        # Main recursive loop
        if isinstance(struct, list):
            cls._branch_from_list(struct, key)
        elif isinstance(struct, dict):
            struct.pop(key, None)
            cls._branch_from_list(struct.values(), key)
        else:
            pass
        return struct

    @classmethod
    def _branch_from_list(cls, datalist, key):
        for obj in datalist:
            cls.strip_key(obj, key)

class NonserializableTypeConverter(object):
    """Crawls a python data structure and
    converts non-serializable data types
    into a serializable type
    """
    special_type_converters = {
        datetime.datetime: lambda x: x.isoformat(),
        uuid.UUID: lambda x: uuid.UUID(str(x)).hex
        }

    @classmethod
    def convert(cls, obj):
        if type(obj) in cls.special_type_converters.keys():
            obj = cls.special_type_converters[type(obj)](obj)
        return obj
    
    @classmethod
    def convert_struct(cls, obj):
        #Main recursive loop
        if isinstance(obj, list):
            cls._branch_from_list(obj)
        elif isinstance(obj, dict):
            for key in obj.keys():
                obj[key] = cls.convert_struct(obj[key])
        else:
            if type(obj) in cls.special_type_converters.keys():
                obj = cls.convert(obj)
        return obj

    @classmethod
    def _branch_from_list(cls, datalist):
        for i in range(len(datalist)):
            datalist[i] = cls.convert_struct(datalist[i])

class StripBlanks(object):
    """Crawls a python data structure and removes
    any keys with values None, [], or {}
    """

    @classmethod
    def strip_blanks(cls, obj):
        # Main recursive loop
        if isinstance(obj, list):
            cls._branch_from_list(obj)
        elif isinstance(obj, dict):
            cls._branch_from_list(obj.values())
            to_remove = []
            for (key, value) in obj.iteritems():
                if value in [None, [], '']:
                    to_remove.append(key)
            for key in to_remove:
                obj.pop(key)
        else:
            pass
        return obj

    @classmethod
    def _branch_from_list(cls, datalist):
        for struct in datalist:
            cls.strip_blanks(struct)

class IdCalculator:
    """
    Calculates a unique hash for a data struct.
    Any value with the key id_key is discarded.
    """

    def __init__(self, data_struct, id_key):
        data_struct_copy = copy.deepcopy(data_struct)
        self._data_struct = self._process_data_struct(data_struct_copy, id_key)

    def _process_data_struct(self, data_struct, id_key):
        data_struct_without_ids = StripKey.strip_key(data_struct, id_key)
        data_struct_without_blanks = StripBlanks.strip_blanks(
            data_struct_without_ids)
        return data_struct_without_blanks
        
    def get_id(self):
        return self._calculate_id(self._data_struct)

    @classmethod
    def _calculate_id(cls, data_struct):
        data_json = struct_to_json(data_struct)
        return hashlib.sha256(data_json).hexdigest()
