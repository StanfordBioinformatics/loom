# DataObject and related objects

unnamed_file_content = {
    'hash_value': '1234asfd',
    'hash_function': 'md5', 
}

file_content = {
    'filename': 'file1.txt',
    'unnamed_file_content': unnamed_file_content,
}

unnamed_file_content2 = {
    'hash_value': 'xyz123',
    'hash_function': 'md5',
}

file_content_2 = {
    'filename': 'file2.txt',
    'unnamed_file_content': unnamed_file_content2,
}

file = {
    'file_content': file_content,
}

file_2 = {
    'file_content': file_content_2,
}

file_location = {
    'unnamed_file_content': unnamed_file_content,
    'url': 'file:///absolute/path/to/my/file.txt',
}

file_location_2 = {
    'unnamed_file_content': unnamed_file_content2,
    'url': 'file:///absolute/path/to/my/file2.txt',
}

file_import = {
    'file_data_object': file,
    'note': 'Here is where I got this',
    'source_url': 'file:///data/data/data/data.dat',
}

integer_data_object = {
    'integer_content': {
        'integer_value': 3
    }
}

boolean_data_object = {
    'boolean_content': {
        'boolean_value': True
    }
}

string_data_object = {
    'string_content': {
        'string_value': 'some text here'
    }
}

json_data_object = {
    'json_content': {
        'json_value': {"data": "some text here"}
    }
}

