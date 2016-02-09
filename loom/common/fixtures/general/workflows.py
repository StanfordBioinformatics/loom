from .data_objects import file_struct

# Step and related objects

input_port_1a_struct = {
    'name': 'input_port1a',
    'file_name': 'one.txt',
    'is_array': False
    }

input_port_1b_struct = {
    'name': 'input_port1b',
    'file_name': 'two.txt',
    'is_array': False,
    }

output_port_1_struct = {
    'name': 'output_port1',
    'file_name': 'one_two.txt',
    'is_array': False,
    }

input_port_2_struct = {
    'name': 'input_port2',
    }

output_port_2_struct = {
    'name': 'output_port2',
    'file_name': 'one_two_three.txt',
    }

port_identifier_struct = {
    'step': 'step1',
    'port': 'input_port1a',
    }

data_binding_struct = {
    'data_object': file_struct,
    'destination': {
        'step': 'step1',
        'port': 'input_port1a',
        },
    }

data_pipe_struct = {
    'source': {
        'step': 'step1',
        'port': 'output_port1',
        },
    'destination': {
        'step': 'step2',
        'port': 'input_port2',
        },
    }

resource_set_struct = {
    'memory': '5G',
    'cores': 4,
    }

docker_image_struct = {
    'docker_image': '1234567asdf',
    }

step_1_struct = {
    'name': 'step1',
    'input_ports': [input_port_1a_struct],
    'output_ports': [output_port_1_struct],
    'command': 'echo hello',
    'environment': docker_image_struct,
    'resources': resource_set_struct,
    }

step_2_struct = {
    'name': 'step2',
    'input_ports': [input_port_2_struct],
    'output_ports': [output_port_2_struct],
    'command': 'echo world',
    'environment': docker_image_struct,
    'resources': resource_set_struct,
    }

workflow_struct = {
    'steps': [step_1_struct, step_2_struct],
    'data_bindings': [data_binding_struct],
    'data_pipes': [data_pipe_struct],
    }

step_with_templated_command_struct = {
    'name': 'step1',
    'constants': {'id': 'step123'},
    'input_ports': [input_port_1a_struct],
    'output_ports': [output_port_1_struct],
    'command': 'cat {{ input_ports.input_port1a.file_name }} > {{ output_ports.output_port1.file_name }};'+
               ' echo {{ constants.id }}{{ constants.wf }}{{ constants.rs }} >>  {{ output_ports.output_port1.file_name }}',
    'environment': docker_image_struct,
    'resources': resource_set_struct,
    }

workflow_with_templated_command_struct = {
    'steps': [step_with_templated_command_struct],
    'constants': {
        'id': 'workflow123',
        'wf': 'x',
        }
    }
