data_tree_schema = {
    # schema used to verify that data contains only a X,
    # a list of X, or a list of (lists of)^n X,
    # where X is string, integer, float, boolean, or object.
    # These are the only valid structures for user-provided 
    # data values, e.g. 'file.txt@id',
    # '["file1.txt@id1", "file2.txt@id2"]', or
    # '[["file1.txt@id1", "file2.txt@id2"], ["file3.txt@id3"]]'.
    # A DataObject may be used rather than the primitive type.
    'definitions': {
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
                { 'type': [ 'object' ],
                  'properties': {
                      'type': {'enum': ['boolean']}
                  },
                  'required': ['type']},
                { 'type': ['array'], 
                  'items': {
                      '$ref': '#/definitions/booleanschema'}}
            ]
        }
    },
    'anyOf': [
        {'$ref': '#/definitions/stringschema'},
        {'$ref': '#/definitions/integerschema'},
        {'$ref': '#/definitions/floatschema'},
        {'$ref': '#/definitions/booleanschema'},
    ]
}
