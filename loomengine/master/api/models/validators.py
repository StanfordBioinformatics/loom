# TEMPLATES

def template_import_validator(value):
    pass

def workflow_outputs_validator(value):
    pass

def workflow_inputs_validator(value):
    pass

def step_environment_validator(value):
    pass

def step_outputs_validator(value):
    # TODO validate other fields

    for output in value:
        parser = output.get('parser')
        task_output_parser_validator(parser)

def step_inputs_validator(value):
    pass

def step_resources_validator(value):
    pass

def channel_bindings_validator(value):
    # channel_bindings is a list of dicts the form
    # [{'step': String, 'bindings': ListOfBindings},...]
    # ListOfBindings is a list of internal:external channel names, e.g.
    # ["internal_channel1:external_channel1","internal_channel2:external_channel2"]
    pass

# TASKS

def _delimited_output_parser_validator(options):
    if not options:
        raise ValidationError("parser 'options' field is required for this type")
    try:
        delimiter = options.get('delimiter')
    except AttributeError:
        raise ValidationError("parser 'options' not a valid dict: '%s'" % options)
    invalid_fields = set(options.keys()).difference(set(['delimiter', 'trim']))
    if invalid_fields:
        raise ValidationError("parser option(s) '%s' not allowed for this parser type"
                              % "', '".join(invalid_fields))

PARSER_TYPES = {
    'delimited': _delimited_output_parser_validator
}

def task_output_parser_validator(value):
    # Empty is ok
    if not value:
        return

    # but otherwise it must be a dict and needs a valid type
    try:
        parser_type = value.get('type')
    except AttributeError:
        raise ValidationError("'%s' is not a valid JSON dict." % value)
    if not parser_type:
        raise ValidationError("Parser is missing 'type' field")
    elif parser_type not in PARSER_TYPES.keys():
        raise ValidationError("Invalid parser type '%s'. Valid types are '%s'"
                              % (parser_type, "', '".join(PARSER_TYPES.keys())))
    # It may have options
    options = value.get('options')

    # but no other fields are allowed
    invalid_fields = set(value.keys()).difference(set(['type', 'options']))
    if invalid_fields:
        raise ValidationError(
            "Parser has invalid field(s) '%s'" % "', '".join(invalid_fields))

    # Perform further validation specific to parser_type
    type_specific_validator = PARSER_TYPES[parser_type]
    type_specific_validator(options)

def task_data_path_validator(value):
    try:
        for (index, degree) in value:
            if not (isinstance(index, (int,long)) and isinstance(degree, (int,long))):
                raise ValidationError('Value must be a list of (int, int) tuples')
    except TypeError:
        raise ValidationError('Value must be a list of (int, int) tuples')
