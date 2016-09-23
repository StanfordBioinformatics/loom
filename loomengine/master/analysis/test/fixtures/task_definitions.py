from .data_objects import file_data_object, string_data_object

# TaskDefinition and related objects

task_definition_docker_environment = {
    'docker_image': '1234567asdf',
}

task_definition_input = {
    'data_object_content': string_data_object['string_content'],
    'type': 'string'
}

task_definition_output = {
    'filename':'here.out',
    'type': 'string'
}

task_definition = {
    'inputs': [task_definition_input],
    'outputs': [task_definition_output],
    'command': 'echo test > here.out',
    'environment': task_definition_docker_environment,
}
