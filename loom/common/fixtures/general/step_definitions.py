from data_objects import file_struct

# StepDefinition and related objects

docker_image_struct = {
    'docker_image': '1234567asdf',
    }

step_definition_input_port_struct = {
    'file_names':[{'name': 'copy/my/file/here.txt'}],
    "is_array": False,
    "data_object": file_struct
    }

step_definition_output_port_struct = {
    'file_name':'look/for/my/file/here.txt',
    "is_array": False
    }

step_definition_struct = {
    'input_ports': [step_definition_input_port_struct],
    'output_ports': [step_definition_output_port_struct],
    'command': 'echo test',
    'environment': docker_image_struct,
    }
