""" Fixtures for DataObject and related objects
"""

integer_data_object = {
    'type': 'integer',
    'value': 3
}

boolean_data_object = {
    'type': 'boolean',
    'value': True
}

float_data_object = {
    'type': 'float',
    'value': 2.7
}

string_data_object = {
    'type': 'string',
    'value': 'some text here'
}

file_data_object = {
    'type': 'file',
    'value': {
        'filename': 'file1.txt',
        'md5': 'eed7ca1bba1c93a7fa5b5dba1307b791',
        'import_comments': 'Here is where I got this',
        'source_type': 'imported',
        'imported_from_url': 'file:///data/data/data/data.dat',
    }
}
