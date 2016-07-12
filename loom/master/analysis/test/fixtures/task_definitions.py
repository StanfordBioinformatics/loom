from .data_objects import file, string_data_object

# TaskDefinition and related objects

docker_image = {
    'docker_image': '1234567asdf',
}

task_definition_input = {
    "data_object_content": string_data_object['string_content']
}

task_definition_output = {
    'filename':'here.out',
}

task_definition = {
    'inputs': [task_definition_input],
    'outputs': [task_definition_output],
    'command': 'echo test > here.out',
    'environment': docker_image,
}
