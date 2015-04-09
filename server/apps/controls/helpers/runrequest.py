import collections
import json
import jsonschema

from apps.controls.helpers.links import Linker
from apps.controls.helpers.objtools import StripKeys
from apps.controls.helpers.substitution import Substitution
from apps.controls.helpers import schema

class RunRequestValidationError(Exception):
    pass

class RunRequestHelper(object):

    schema = schema.RunRequestSchema

    @classmethod
    def clean_json(cls, raw_data_json):
        data_obj = json.loads(
            raw_data_json, 
            object_pairs_hook=collections.OrderedDict)
#        cls._validate_raw_data_json(data_obj)
        cls._resolve_links(data_obj)
        cls._apply_constants(data_obj)
#        cls._strip_comments(data_obj)
#        cls._validate_clean_data_json(data_obj)
        clean_data_json = json.dumps(data_obj, sort_keys=True, 
                                     indent=4, separators=(',', ': '))
        return clean_data_json

    @classmethod
    def _validate_raw_data_json(cls, data_json):
        try:
            jsonschema.validate(data_json, cls.schema.RAW)
        except jsonschema.ValidationError as e:
            raise RunRequestValidationError(e.message)

    @classmethod
    def _validate_clean_data_json(cls, data_json):
        try:
            jsonschema.validate(data_json, cls.schema.CLEAN)
        except jsonschema.ValidationError as e:
            raise RunRequestValidationError(e.message)

    @classmethod
    def _apply_constants(cls, data_obj):
        Substitution.apply_constants(data_obj)

    @classmethod
    def _resolve_links(cls, data_obj):
        Linker().resolve_links(data_obj)

    @classmethod
    def _strip_comments(cls, data_obj):
        StripKeys.strip_keys(data_obj, ['comment'])
