# DataObject and related objects

file_contents_obj = {
    'hash_value': '1234asfd',
    'hash_function': 'md5', 
    }

file_contents_obj_2 = {
    'hash_value': 'xyz123',
    'hash_function': 'md5',
    }

file_obj = {
    'file_contents': file_contents_obj,
    }

file_obj_2 = {
    'file_contents': file_contents_obj_2,
    }

file_array_obj = {
    'files': [
        file_obj,
        file_obj_2
        ]
    }

server_file_storage_location_obj = {
    'file_contents': file_contents_obj,
    'file_path': '/absolute/path/to/my/file.txt',
    'host_url': 'localhost',
    }

server_file_storage_location_obj_2 = {
    'file_contents': file_contents_obj_2,
    'file_path': '/absolute/path/to/my/file2.txt',
    'host_url': 'localhost',
    }
