import json
import collections
import string
from copy import copy

class ConstantSubstitutionHelper(object):

    """
    This class takes a JSON string or python object as input and substitutes constant values in
    strings throughout the data structure according to particular rules.
        input: json string
        output: dict containing a tree structure of dicts, arrays, and scalar primitives
        entry point: ConstantSubstitutionHelper.apply_constants_in_json(data_json)

    Constants defined as a dict under a "constants" key will be applied
    to all strings at or below the level of the dict with "constants".

    Constants are applied in order, even in the same constants dict a
    later constant may substitute an earlier one, but not vice versa.
    e.g. {"constants": {"sampleID": "X25", "caseID": "$sampleID_pilot"}, ...}

    File id's are also used as variable names, and will be substituted for the
    path, as in this definition:

    "files": [{'id': 'input_from_joe', 'path': 'data/input.csv'}, {...}, ...]

    Again, substitutions are applied in order through the file list, and
    available for all levels at or lower from the dict containing "files".

    Constants are processed before files at the same level, so constants may
    be used in defining file path or id, but files cannot be used to
    define constants at the same level.
    """

    CONSTANT_DICT_KEY = 'constants'
    FILE_LIST_KEY = 'files'
    FILE_KEY_FIELD = 'id'
    FILE_VALUE_FIELD = 'path'

    @classmethod
    def apply_constants_in_json(cls, data_json):
        data_obj = json.loads(
            data_json, 
            # Use ordered dict to ensure order is maintained
            # in a dict. Earlier items can define constants
            # used by later items in the same dict.
            object_pairs_hook=collections.OrderedDict
        )
        return cls.apply_constants(data_obj)

    @classmethod
    def apply_constants(cls, obj, constant_dict=None):
        """
        Apply constants in any object type. 
        Nested objects will recurse with this function.
        """

        # constant_dict accumulates constants from the root to the leaves of the structure.
        # values may be overwritten as we traverse toward leaves.
        if constant_dict is None:
            constant_dict = {}

        if cls._is_string(obj):
            return cls._apply_constants_to_string(obj, constant_dict)
        elif cls._is_list(obj):
            return cls._apply_constants_to_list(obj, constant_dict)
        elif cls._is_dict(obj):
            return cls._apply_constants_to_dict(obj, constant_dict)
        else:
            return obj

    @classmethod
    def _apply_constants_to_string(cls, obj, constant_dict):
        # "$const" or "${const} replaced by dict value for "const"
        t = string.Template(obj)
        return t.substitute(constant_dict)

    @classmethod
    def _apply_constants_to_list(cls, obj, constant_dict):
        for i in range(len(obj)):
            # copy() constant_dict for each branch so that definitions added on
            # one branch do not apply to the others.
            obj[i] = cls.apply_constants(obj[i], copy(constant_dict))
        return obj

    @classmethod
    def _apply_constants_to_dict(cls, obj, constant_dict):
        # Add new values to constant_dict from constants and files
        cls._process_new_constants(obj, constant_dict)
        cls._process_constants_from_file_ids(obj, constant_dict)

        for (key, value) in obj.iteritems():
            obj[key] = cls.apply_constants(value, copy(constant_dict))
        return obj

    @classmethod
    def _process_new_constants(cls, obj, constant_dict):
        new_constants = obj.pop(cls.CONSTANT_DICT_KEY, {})
        cls._insert_new_constants(new_constants, constant_dict)

    @classmethod
    def _process_constants_from_file_ids(cls, obj, constant_dict):
        if not obj.has_key(cls.FILE_LIST_KEY):
            return
        # If {"files":{...}} is defined, treat id -> path as a definition for a constant.
        for thisfile in obj[cls.FILE_LIST_KEY]:
            key = thisfile.get(cls.FILE_KEY_FIELD)
            value = thisfile.get(cls.FILE_VALUE_FIELD)
            if (key is not None) and (value is not None):
                cls._insert_new_constant(key, value, constant_dict)

    @classmethod
    def _insert_new_constants(cls, new_constants, constant_dict):
        for (key, raw_value) in new_constants.iteritems():
            cls._insert_new_constant(key, raw_value, constant_dict)

    @classmethod
    def _insert_new_constant(cls, key, raw_value, constant_dict):
        # Aply substitutions to string before recording in constant_dict
        value = cls._apply_constants_to_string(raw_value, constant_dict)
        constant_dict.update({key: value})

    @classmethod
    def _pop_new_constants(cls, obj):
        # After we use constants to make substitutions, the data structure we return 
        # won't have 'constants' defined anymore.
        new_constants = obj.pop(cls.CONSTANT_DICT_KEY, {})
        if cls._is_dict(new_constants):
            return new_constants
        else:
            return {}
    
    @classmethod
    def _is_string(cls, obj):
        return isinstance(obj, basestring)

    @classmethod
    def _is_list(cls, obj):
        return isinstance(obj, (list, tuple))

    @classmethod
    def _is_dict(cls, obj):
        # True for OrderedDict
        return hasattr(obj, 'keys') and hasattr(obj, 'values')
