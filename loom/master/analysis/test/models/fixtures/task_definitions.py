from .data_objects import file

# TaskDefinition and related objects

docker_image = {
    'docker_image': '1234567asdf',
}

task_definition_input = {
    "data_object": file
}

task_definition_output = {
    'path':'here.out',
}

task_definition = {
    'inputs': [task_definition_input],
    'outputs': [task_definition_output],
    'command': 'echo test > here.out',
    'environment': docker_image,
}
