import copy
import datetime
import hashlib
import json
import uuid

from .exceptions import *


JSON_DUMP_OPTIONS = {'separators': (',',':'), 'sort_keys': True}

def obj_to_json(data_obj):
    try:
        data_obj = NonserializableTypeConverter.convert_struct(data_obj)
        return json.dumps(data_obj, **JSON_DUMP_OPTIONS)
    except Exception as e:
        raise ConvertToJsonError('Could not convert object to JSON. "%s". %s' % (data_obj, e.message))

def json_to_obj(data_json):
    try:
        data_obj =json.loads(data_json)
    except Exception as e:
        raise InvalidJsonError('Invalid JSON. "%s". %s' % (data_json, e.message))
    return data_obj


class StripKey(object):
    """
    Crawls a python data structure and removes
    any data with the designated key name
    """

    @classmethod
    def strip_key(cls, obj, key):
        # Main recursive loop
        if isinstance(obj, list):
            cls._branch_from_list(obj, key)
        elif isinstance(obj, dict):
            obj.pop(key, None)
            cls._branch_from_list(obj.values(), key)
        else:
            pass
        return obj

    @classmethod
    def _branch_from_list(cls, objlist, key):
        for obj in objlist:
            cls.strip_key(obj, key)

class NonserializableTypeConverter(object):
    """Crawls a python data structure and
    converts non-serializable data types
    into a serializable type
    """
    special_type_converters = {
        datetime.datetime: lambda x: x.isoformat(),
        uuid.UUID: str
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
                obj = cls.special_type_converters[type(obj)](obj)
#            obj = cls.convert(obj)
        return obj

    @classmethod
    def _branch_from_list(cls, objlist):
        for i in range(len(objlist)):
            objlist[i] = cls.convert_struct(objlist[i])

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
    def _branch_from_list(cls, objlist):
        for obj in objlist:
            cls.strip_blanks(obj)

class IdCalculator:
    """
    Calculates a unique hash for a data object.
    Any value with the key id_key is discarded.
    Lists are sorted by their unique hash.
    """

    def __init__(self, data_obj, id_key):
        data_obj_copy = copy.deepcopy(data_obj)
        self._data_obj = self._process_data_obj(data_obj_copy, id_key)

    def _process_data_obj(self, data_obj, id_key):
        data_obj_without_ids = StripKey.strip_key(data_obj, id_key)
        data_obj_without_blanks = StripBlanks.strip_blanks(data_obj_without_ids)
        return self._sort_by_id(data_obj_without_blanks)
        
    def get_id(self):
        return self._calculate_id(self._data_obj)

    @classmethod
    def _calculate_id(cls, data_obj):
        data_json = obj_to_json(data_obj)
        return hashlib.sha256(data_json).hexdigest()

    @classmethod
    def _sort_by_id(cls, obj):
        # Main recursive loop
        if isinstance(obj, list):
            for item in obj:
                cls._sort_by_id(item)
            obj.sort(key=lambda item: cls._calculate_id(item))
        elif isinstance(obj, dict):
            for item in obj.values():
                cls._sort_by_id(item)
        else:
            return obj
        return obj
