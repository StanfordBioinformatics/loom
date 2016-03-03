from data_objects import file_struct

# TaskDefinition and related objects

docker_image_struct = {
    'docker_image': '1234567asdf',
}

task_definition_input_struct = {
    "type": "file",
    "name": "data_file_in",
    "data_object": file_struct
}

task_definition_output_file_struct = {
    "type": "file",
    'name': 'file_out',
    'path':'here.out',
}

step_definition_output_file_array_struct = {
    'type': 'file_array',
    'name': 'array_files_out',
    'path': ['here.txt', 'there.txt']
}

step_definition_output_file_array_2_struct = {
    'type': 'file_array',
    'name': 'array_files_out',
    'path': '*.out'
}

task_definition_struct = {
    'inputs': [step_definition_input_struct],
    'outputs': [step_definition_output_struct],
    'command': 'echo test',
    'environment': docker_image_struct,
}
