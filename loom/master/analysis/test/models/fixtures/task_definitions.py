from data_objects import file_struct

# TaskDefinition and related objects

docker_image_struct = {
    'docker_image': '1234567asdf',
}

task_definition_input_struct = {
    "data_object": file_struct
}

task_definition_output_struct = {
    'path':'here.out',
}

task_definition_struct = {
    'inputs': [task_definition_input_struct],
    'outputs': [task_definition_output_struct],
    'command': 'echo test > here.out',
    'environment': docker_image_struct,
}
