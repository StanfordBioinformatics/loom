from django.core.exceptions import ValidationError
import jsonschema
import jsonschema.exceptions
import re
import urlparse


class DataObjectValidator(object):

    @classmethod
    def _validate_boolean_data(cls, value):
        schema = {"type": "object",
                  "properties": {"value": {"type": "boolean"}},
                  "required": ["value"]}
        try:
            jsonschema.validate(value, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(e.message)

    @classmethod
    def _validate_file_data(cls, value):
        if value != '':
            raise ValidationError(
                '"value" field should be blank for "file" DataObjects. '\
                'Instead found "%s".' % value)

    @classmethod
    def _validate_float_data(cls, value):
        schema = {"type": "object",
                  "properties": {"value": {"type": "number"}},
                  "required": ["value"]}
        try:
            jsonschema.validate(value, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(e.message)

    @classmethod
    def _validate_integer_data(cls, value):
        schema = {"type": "object",
                  "properties": {"value": {"type": "number"}},
                  "required": ["value"]}
        try:
            jsonschema.validate(value, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(e.message)

    @classmethod
    def _validate_string_data(cls, value):
        schema = {"type": "object",
                  "properties": {"value": {"type": "string"}},
                  "required": ["value"]}
        try:
            jsonschema.validate(value, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(e.message)

    @classmethod
    def validate_model(cls, instance):
        DATA_VALIDATORS = {
            'boolean': cls._validate_boolean_data,
            'file': cls._validate_file_data,
            'float': cls._validate_float_data,
            'integer': cls._validate_integer_data,
            'string': cls._validate_string_data,
        }
        if not instance.type in DATA_VALIDATORS.keys():
            # This should be caught in field validation
            return
        validate_data = DATA_VALIDATORS[instance.type]
        validate_data(instance.data)

def validate_tag(tag_model):
    for type in ('file', 'template', 'run'):
        if tag_model.type == type and getattr(tag_model, type) is None:
            raise ValidationError('Tag has no %s' % type)
        if tag_model.type != type and getattr(tag_model, type) is not None:
            raise ValidationError('Tag is type %s but is linked to a %s'
                                  % (tag_model.type, type))

def validate_filename(value):
    pattern = r'^([a-zA-Z0-9_]|[a-zA-Z0-9._][a-zA-Z0-9.\-_]+)$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Invalid filename "%s". Only alphanumberic characters, '
            '".", "-", and "_" are allowed.' % value)

def validate_relative_file_path(value):
    if not value:
        return
    if value.startswith('/'):
        raise ValidationError('Invalid relative path "%s". '\
                              'Relative path must not start with "/"')
    if value.endswith('/'):
        raise ValidationError('Invalid file path "%s". '\
                              'File path must not end with "/"')
    for part in value.split('/'):
        pattern = r'^([a-zA-Z0-9_]|[a-zA-Z0-9._][a-zA-Z0-9.\-_]+)$'
        if not re.match(pattern, part):
            raise ValidationError(
                'Invalid file or directory name "%s". Only alphanumberic characters, '
                '".", "-", and "_" are allowed.' & part)

def validate_md5(value):
    pattern = r'^[0-9a-z]{32}$'
    if not re.match(pattern, value):
        raise ValidationError('Invalid md5 value "%s"' % value)
    
def validate_url(value):
    url = urlparse.urlparse(value)
    if not re.match(r'[A-Za-z]+', url.scheme):
        raise ValidationError(
            'Invalid scheme "%s" in URL "%s"' % (url.scheme, value))
    if not re.match(r'[0-9A-Za-z.\-_\/]+', url.path):
        raise ValidationError(
            'Invalid path "%s" in URL "%s"' % (url.path, value))

def validate_environment(value):
    schema = {
        "type": "object",
        "properties": {"docker_image": {"type": "string"}},
        "required": ["docker_image"]
    }

    try:
        jsonschema.validate(value, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(e.message)

def validate_resources(value):
    schema = {
        "type": "object",
        "properties": {
            "cores": {"oneOf": [
                {"type" : "string"},
                {"type" : "integer"}
            ]},
            "disk_size": {"oneOf": [
                {"type" : "string"},
                {"type" : "integer"}
            ]},
            "memory": {"oneOf": [
                {"type" : "string"},
                {"type" : "integer"}
            ]}
        }
    }
    try:
        jsonschema.validate(value, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(e.message)
    cores = value.get('cores')
    if cores is not None:
        if not re.match(r'^[0-9]*$', str(cores)):
            raise ValidationError(
                'Invalid value for "cores: "%s". Expected an integer.')
    disk_size = value.get('disk_size')
    if disk_size is not None:
        if not re.match(r'^[0-9]*$', str(disk_size)):
            raise ValidationError(
                'Invalid value for "disk_size: "%s". Expected an integer (in GB).')
    memory = value.get('memory')
    if memory is not None:
        if not re.match(r'^[0-9]*$', str(memory)):
            raise ValidationError(
                'Invalid value for "memory: "%s". Expected an integer (in GB).')

def validate_notification_addresses(value):
    # value should be a list of notification targets,
    # either email addresses or http/https URLs.
    for target in value:
        match = re.match(r'(^\S+@\S+$|^https?://|^HTTPS?://)', target)
        if match is None:
            raise ValidationError(
                'Invalid notification target, must be an email address '\
                'or an http/https URL: "%s"' % target)

def validate_notification_context(value):
    schema = {
        "type": "object",
        "properties": {"server_name": {"type": "string"},
                       "server_url": {"type": "string"}},
        "required": ["server_name"]
    }
    try:
        jsonschema.validate(value, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(e.message)

class OutputParserValidator(object):

    @classmethod
    def _validate_delimited_output_parser_options(cls, value):
        schema = {
            "type": "object",
            "properties": {"delimiter": {"type": "string"},
                           "trim": {"type": "string"}
            }
        }

    @classmethod
    def validate_output_parser(cls, value):
        OPTIONS_VALIDATORS = {
            'delimited': cls._validate_delimited_output_parser_options
        }

        schema = {
            "type": "object",
            "properties": {"type": {"type": "string",
                                    "enum": ["delimited"]},
                           "options": {"type": "object"}
            },
            "required": ["type"]
        }
        try:
            jsonschema.validate(value, schema)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(e.message)
    
        # Validate options specific to parser_type
        if value.get('options'):
            validate_options = OPTIONS_VALIDATORS[value.get('type')]
            validate_options(value.get('options'))


def validate_data_path(value):
    schema = {
        "type": "array",
        "items": {
            "type": "array",
            "items": [{"type": "integer"},
                      {"type": "integer"}]
        }
    }
    try:
        jsonschema.validate(value, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(e.message)

    
class TemplateValidator(object):

    @classmethod
    def validate_name(cls, value):
        # Template names are used in file paths,
        # so we apply the same restrictions.
        pattern = r'^([a-zA-Z0-9_]|[a-zA-Z0-9._][a-zA-Z0-9.\-_]+)$'
        if not re.match(pattern, value):
            raise ValidationError(
                'Invalid template name "%s". Only alphanumberic characters, '
                '".", "-", and "_" are allowed.' & value)

    @classmethod
    def validate_outputs(cls, value):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "as_channel": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["file", "boolean", "string", "float", "integer"]},
                    "mode": {"type": "string"},
                    "source": {
                        "type": "object",
                        "properties": {
                            "stream": {"type": "string",
                                       "enum": ["stdout", "stderr"]},
                            "filename": {"type": "string"},
                            "filenames": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array",
                                     "items": {"type": "string"}}
                                ]},
                            "glob": {"type": "string"}
                        }
                    },
                    "parser": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "options": {"type": "object"}
                        }
                    }
                },
                "required" : ["type", "channel"]
            }
        }
        try:
            jsonschema.validate(value, schema)
	except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(e.message)

def validate_ge0(value):
    if value < 0:
        raise ValidationError('Must be >= 0. Invalid value "%s"' % value)

data_node_schema = {
    # schema used to verify that data contains only a X,
    # a list of X, or a list of (lists of)^n X,
    # where X is string, integer, float, boolean, or object.
    # These are the only valid structures for user-provided 
    # data values, e.g. 'file.txt@id',
    # '["file1.txt@id1", "file2.txt@id2"]', or
    # '[["file1.txt@id1", "file2.txt@id2"], ["file3.txt@id3"]]'.
    # A DataObject may be used rather than the primitive type.
    'definitions': {
        'referenceschema': {
            'oneOf': [
                {
                    'type': [ 'object' ],
                    'properties': {
                        'uuid': { 'type': 'string' }
                    },
                    'required': ['uuid'],
                    'additionalProperties': True,
                },
                { 'type': ['array'], 
                  'items': {
                      '$ref': '#/definitions/referenceschema'}}
            ]
        },
        'stringschema': {
            'oneOf': [
                { 'type': [ 'string' ] },
                { 'type': [ 'object' ],
                  'properties': {
                      'type': {'enum': ['string']}
                  },
                  'required': ['type']},
                { 'type': ['array'], 
                  'items': {
                      '$ref': '#/definitions/stringschema'}}
            ]
        },
        'integerschema': {
            'oneOf': [
                { 'type': [ 'integer' ] },
                { 'type': [ 'object' ],
                  'properties': {
                      'type': {'enum': ['integer']}
                  },
                  'required': ['type']},
                { 'type': ['array'], 
                  'items': {
                      '$ref': '#/definitions/integerschema'}}
            ]
        },
        'floatschema': {
            'oneOf': [
                { 'type': [ 'number' ] },
                { 'type': [ 'object' ],
                  'properties': {
                      'type': {'enum': ['float']}
                  },
                  'required': ['type']},
                { 'type': ['array'], 
                  'items': {
                      '$ref': '#/definitions/floatschema'}}
            ]
        },
        'booleanschema': {
            'oneOf': [
                { 'type': [ 'boolean' ] },
                { 'type': [ 'string' ] },
                { 'type': [ 'object' ],
                  'properties': {
                      'type': {'enum': ['boolean']}
                  },
                  'required': ['type']},
                { 'type': ['array'], 
                  'items': {
                      '$ref': '#/definitions/booleanschema'}}
            ]
        },
        'fileschema': {
            'oneOf': [
                { 'type': [ 'string' ] },
                { 'type': [ 'object' ],
                  'properties': {
                      'type': {'enum': ['file']}
                  },
                  'required': ['type']},
                { 'type': ['array'], 
                  'items': {
                      '$ref': '#/definitions/fileschema'}}
            ]
        },
    },
    'anyOf': [
        {'$ref': '#/definitions/referenceschema'},
        {'$ref': '#/definitions/stringschema'},
        {'$ref': '#/definitions/integerschema'},
        {'$ref': '#/definitions/floatschema'},
        {'$ref': '#/definitions/booleanschema'},
        {'$ref': '#/definitions/fileschema'},
    ]
}
