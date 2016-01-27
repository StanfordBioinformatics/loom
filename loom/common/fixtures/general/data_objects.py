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
    'file_contents': file_contents_struct,
    }

file_struct_2 = {
    'file_contents': file_contents_struct_2,
    }

file_array_struct = {
    'files': [
        file_struct,
        file_struct_2
        ]
    }

server_file_storage_location_struct = {
    'file_contents': file_contents_struct,
    'file_path': '/absolute/path/to/my/file.txt',
    'host_url': 'localhost',
    }

server_file_storage_location_struct_2 = {
    'file_contents': file_contents_struct_2,
    'file_path': '/absolute/path/to/my/file2.txt',
    'host_url': 'localhost',
    }
