""" Fixtures for DataObject and related objects
"""

integer_data_object = {
    'type': 'integer',
    'contents': 3
}

boolean_data_object = {
    'type': 'boolean',
    'contents': True
}

float_data_object = {
    'type': 'float',
    'contents': 2.7
}

string_data_object = {
    'type': 'string',
    'contents': 'some text here'
}

file_data_object = {
    'type': 'file',
    'contents': {
        'filename': 'file1.txt',
        'md5': 'eed7ca1bba1c93a7fa5b5dba1307b791',
        'import_comments': 'Here is where I got this',
        'source_type': 'imported',
        'imported_from_url': 'file:///data/data/data/data.dat',
    }
}
