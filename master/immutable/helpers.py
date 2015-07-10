import copy
import hashlib
import json
from immutable.exceptions import *


JSON_DUMP_OPTIONS = {'separators': (',',':'), 'sort_keys': True}

def obj_to_json(data_obj):
    try:
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

class StripBlanks(object):
    """
    Crawls a python data structure and removes
    any keys with values None, [], or {}
    """

    @classmethod
    def strip_blanks(cls, obj):
        # Main recursive loop
        if isinstance(obj, list):
            cls._branch_from_list(obj)
        elif isinstance(obj, dict):
            to_remove = []
            for (key, value) in obj.iteritems():
                if value in [None, [], {}]:
                    to_remove.append(key)
            for key in to_remove:
                obj.pop(key)
            cls._branch_from_list(obj.values())
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
