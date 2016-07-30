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

file_import = {
    'note': 'Here is where I got this',
    'source_url': 'file:///data/data/data/data.dat',
}

file_import_2 = {
    'note': 'Here is another one',
    'source_url': 'file:///data/data/data/data2.dat',
}

file_location = {
    'status': 'complete',
    'url': 'file:///absolute/path/to/my/file.txt',
}

file_location_2 = {
    'status': 'incomplete',
    'url': 'file:///absolute/path/to/my/file2.txt',
}

file_data_object = {
    'file_content': file_content,
    'file_import': file_import,
    'file_location': file_location
}

file_data_object_without_location = {
    'file_content': file_content,
    'file_import': file_import,
}

file_data_object_without_location_or_content = {
    'file_import': file_import,
}

file_data_object_2 = {
    'file_content': file_content_2,
    'file_import': file_import_2,
    'temp_file_location': file_location_2
}

integer_content = {
    'integer_value': 3
}

integer_data_object = {
    'integer_content': integer_content
}

boolean_content = {
    'boolean_value': True
}

boolean_data_object = {
    'boolean_content': boolean_content
}

string_content = {
    'string_value': 'some text here'
}

string_data_object = {
    'string_content': string_content
}
