from .data_objects import file_obj

# Step and related objects

input_port_1a_obj = {
    'name': 'input_port1a',
    'file_name': 'one.txt',
    'is_array': False
    }

input_port_1b_obj = {
    'name': 'input_port1b',
    'file_name': 'two.txt',
    'is_array': False,
    }

output_port_1_obj = {
    'name': 'output_port1',
    'file_name': 'one_two.txt',
    'is_array': False,
    }

input_port_2_obj = {
    'name': 'input_port2',
    }

output_port_2_obj = {
    'name': 'output_port2',
    'file_name': 'one_two_three.txt',
    }

port_identifier_obj = {
    'step': 'step1',
    'port': 'input_port1a',
    }

data_binding_obj = {
    'data_object': file_obj,
    'destination': {
        'step': 'step1',
        'port': 'input_port1a',
        },
    }

data_pipe_obj = {
    'source': {
        'step': 'step1',
        'port': 'output_port1',
        },
    'destination': {
        'step': 'step2',
        'port': 'input_port2',
        },
    }

resource_set_obj = {
    'memory': '5G',
    'cores': 4,
    }

docker_image_obj = {
    'docker_image': '1234567asdf',
    }

step_1_obj = {
    'name': 'step1',
    'input_ports': [input_port_1a_obj],
    'output_ports': [output_port_1_obj],
    'command': 'echo hello',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }

step_2_obj = {
    'name': 'step2',
    'input_ports': [input_port_2_obj],
    'output_ports': [output_port_2_obj],
    'command': 'echo world',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }

workflow_obj = {
    'steps': [step_1_obj, step_2_obj],
    'data_bindings': [data_binding_obj],
    'data_pipes': [data_pipe_obj],
    }

run_request_obj = {
    'workflows': [workflow_obj],
    'requester': 'someone@example.com',
    }

step_with_templated_command_obj = {
    'name': 'step1',
    'constants': {'id': 'step123'},
    'input_ports': [input_port_1a_obj],
    'output_ports': [output_port_1_obj],
    'command': 'cat {{ input_ports.input_port1a.file_name }} > {{ output_ports.output_port1.file_name }};'+
               ' echo {{ constants.id }}{{ constants.wf }}{{ constants.rs }} >>  {{ output_ports.output_port1.file_name }}',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }

workflow_with_templated_command_obj = {
    'steps': [step_with_templated_command_obj],
    'constants': {
        'id': 'workflow123',
        'wf': 'x',
        }
    }

run_request_with_templated_command_obj = {
    'workflows': [workflow_with_templated_command_obj],
    'constants': {
        'id': 'requestsubmission123',
        'rs': 'y'
        },
    'requester': 'you@there'
    }
