import json

def is_string(obj):
    return isinstance(obj, basestring)

def is_list(obj):
    return isinstance(obj, (list, tuple))

def is_dict(obj):
    return hasattr(obj, 'keys') and hasattr(obj, 'values')


class StripKeys(object):
    """
    Crawls a python data structure and removes
    any data with the designated key name
    """

    @classmethod
    def strip_keys_from_json(cls, json_data, keys):
        data_obj = json.loads(json_data)
        cls.strip_keys(data_obj, keys)
        return data_obj

    @classmethod
    def strip_key_from_json(cls, json_data, key):
        data_obj = json.loads(json_data)
        cls.strip_keys(data_obj, key)
        return data_obj

    @classmethod
    def strip_keys(cls, obj, keys):
        for key in keys:
            cls.strip_key(obj, key)
        return obj

    @classmethod
    def strip_key(cls, obj, key):
        # Main recursive loop
        if is_list(obj):
            cls._branch_from_list(obj, key)
        elif is_dict(obj):
            obj.pop(key, None)
            cls._branch_from_list(obj.values(), key)
        else:
            pass
        return obj

    @classmethod
    def _branch_from_list(cls, objlist, key):
        for obj in objlist:
            cls.strip_key(obj, key)
