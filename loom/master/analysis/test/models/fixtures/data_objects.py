# DataObject and related objects

file_contents_struct = {
    'hash_value': '1234asfd',
    'hash_function': 'md5', 
}

file_contents_struct_2 = {
    'hash_value': 'xyz123',
    'hash_function': 'md5',
}

file_struct = {
    'file_name': 'file1.txt',
    'file_contents': file_contents_struct,
    'metadata': {'arbitrary': 'user', 'defined': 'data'}
}

file_struct_2 = {
    'file_name': 'file2.txt',
    'file_contents': file_contents_struct_2,
    'metadata': {'whatever': 'you', 'want': ['goes', 'here']}
}

file_array_struct = {
    'data_objects': [
        file_struct,
        file_struct_2,
    ]
}

json_struct = {
    'json_data': {'some': 'data', 'and': ['other', 'data']},
}

json_array_struct = {
    'data_objects': [
        json_struct
    ]
}

heterogeneous_array_struct = {
    #This is illegal
    'data_objects': [
        file_struct,
        json_struct
    ]
}

server_storage_location_struct = {
    'file_contents': file_contents_struct,
    'file_path': '/absolute/path/to/my/file.txt',
    'host_url': 'localhost',
}

server_storage_location_struct_2 = {
    'file_contents': file_contents_struct_2,
    'file_path': '/absolute/path/to/my/file2.txt',
    'host_url': 'localhost',
}
