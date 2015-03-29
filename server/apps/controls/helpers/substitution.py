import json
import collections
import string
from copy import copy
from apps.controls.helpers import objtools

class Substitution(object):

    """
    This class takes a JSON string or python object as input and substitutes constant values in
    strings throughout the data structure according to particular rules.

    Constants defined as a dict under a "constants" key will be applied
    to all strings at or below the level of the dict with "constants".
    
    {'pipeline': {'name': '${pi}', 'sessions': [{'constants': {'pi': '3ish'}}]}}
    => Error because pi is undefined for pipeline.name

    {'pipeline': {'sessions': [{'constants': {'pi': '3ish'}, 'name': '${pi}'}]}}
    => {'pipeline': {'sessions': [{'name': '3ish'}]}}

    Constants are applied in order, even in the same constants dict a
    later constant may substitute an earlier one, but not vice versa.
    
    {"constants": {"sampleID": "X25", "caseID": "${sampleID}_pilot"}, "name": "$caseID"}
    => {"name": "X25_pilot"}

    {"constants": {"caseID": "${sampleID}_pilot", "sampleID": "X25"}, "name": "$caseID"}
    => Error because $sampleID undefined for constants.caseID

    File id's are also used as variable names, and will be substituted for the
    path.

    This:
    {"files": [{'id': 'input_from_joe', 'path': 'data/input.csv'}]}

    behaves a lot like this:
    {"constants": {"input_from_joe": "data/input.csv"}}

    As with constants, substitutions are applied in order through the file list, and
    available for all levels at or lower from the dict containing the key "files".

    Constants are processed before files within each level, so constants may
    be used in defining files at the same level, but not vice versa.

    This is meant to be very flexible, e.g. allowing a 'files' dict to appear anywhere in the structure.
    The validation schema will be used to lock down the structure. Hopefully most revisions will affect
    the schema but not the Substitution class.
    """

    # Wherever you find the CONSTANT_DICT_KEY, check for a dict of key:value pairs that serve as constants.
    CONSTANT_DICT_KEY = 'constants'

    # Wherever you find the FILE_LIST_KEY, search for a list of objects with keys FILE_KEY_FIELD and FILE_VALUE_FIELD.
    # The pair FILE_KEY_FIELD.value:FILE_VALUE_FIELD.value define a constant.
    FILE_LIST_KEY = 'files'
    FILE_KEY_FIELD = 'id'
    FILE_VALUE_FIELD = 'path'

    @classmethod
    def apply_constants_in_json(cls, data_json):
        data_obj = json.loads(
            data_json, 
            # Use ordered dict to ensure order is maintained
            # in a dict, so that earlier items can define constants
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

        if objtools.is_string(obj):
            return cls._apply_constants_to_string(obj, constant_dict)
        elif objtools.is_list(obj):
            return cls._apply_constants_to_list(obj, constant_dict)
        elif objtools.is_dict(obj):
            return cls._apply_constants_to_dict(obj, constant_dict)
        else:
            return obj

    @classmethod
    def _apply_constants_to_string(cls, str_value, constant_dict):
        # "$CONST" or "${CONST} replaced by constant_dict value for key 'CONST'
        t = string.Template(str_value)
        # raises KeyError if value not found in dict
        new_str_value = t.substitute(constant_dict)
        return new_str_value

    @classmethod
    def _apply_constants_to_list(cls, list_obj, constant_dict):
        for i in range(len(list_obj)):
            # copy() constant_dict for each branch so that definitions added on
            # one branch do not apply to the others.
            list_obj[i] = cls.apply_constants(list_obj[i], copy(constant_dict))
        return list_obj

    @classmethod
    def _apply_constants_to_dict(cls, dict_obj, constant_dict):
        # Add new values to constant_dict from constants and files
        cls._process_new_constants(dict_obj, constant_dict)
        cls._process_constants_from_files(dict_obj, constant_dict)

        for (key, value) in dict_obj.iteritems():
            dict_obj[key] = cls.apply_constants(value, copy(constant_dict))
        return dict_obj

    @classmethod
    def _process_new_constants(cls, dict_obj, constant_dict):
        new_constants = dict_obj.pop(cls.CONSTANT_DICT_KEY, {})
        cls._insert_new_constants(new_constants, constant_dict)

    @classmethod
    def _process_constants_from_files(cls, dict_obj, constant_dict):
        if not dict_obj.has_key(cls.FILE_LIST_KEY):
            return
        # If {"files":[{"id":...,"path":...},...]} is defined, treat id -> path as a definition for a constant.
        for thisfile in dict_obj[cls.FILE_LIST_KEY]:
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
        # Apply substitutions to string before recording in constant_dict
        value = cls._apply_constants_to_string(raw_value, constant_dict)
        constant_dict.update({key: value})
