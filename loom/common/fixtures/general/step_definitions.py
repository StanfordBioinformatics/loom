from data_objects import file_obj

# StepDefinition and related objects

docker_image_obj = {
    'docker_image': '1234567asdf',
    }

step_definition_input_port_obj = {
    'file_names':[{'name': 'copy/my/file/here.txt'}],
    "is_array": False,
    "data_object": file_obj
    }

step_definition_output_port_obj = {
    'file_name':'look/for/my/file/here.txt',
    "is_array": False
    }

step_definition_obj = {
    'input_ports': [step_definition_input_port_obj],
    'output_ports': [step_definition_output_port_obj],
    'command': 'echo test',
    'environment': docker_image_obj,
    }
