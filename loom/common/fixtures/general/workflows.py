from .data_objects import file_struct

# WorkflowRunRequest and related objects

resource_set_struct = {
    'memory': '5G',
    'cores': 4,
    }

docker_image_struct = {
    'docker_image': '1234567asdf',
    }

step_input_1_struct = {
    'from_channel': 'input1',
    'to_path': 'input1.txt'
}

step_output_1_struct = {
    'from_path': 'output1.txt',
    'to_channel': 'output1'
}

step_output_2_struct = {
    'from_path': 'output2.txt',
    'to_channel': 'output2'
}

step_input_2_struct = {
    'from_channel': 'input2',
    'to_path': 'input2.txt'
}

step_1_struct = {
    'step_name': 'step1',
    'command': 'echo hello',
    'environment': docker_image_struct,
    'resources': resource_set_struct,
    'step_inputs': [step_input_1_struct],
    'step_outputs': [step_output_1_struct]
    }

step_2_struct = {
    'step_name': 'step2',
    'command': 'echo world',
    'environment': docker_image_struct,
    'resources': resource_set_struct,
    'step_inputs': [step_input_2_struct],
    'step_outputs': [step_output_2_struct]
    }

workflow_input_1_struct = {
    'input_name': 'input1',
    'to_channel': 'input1'
}

workflow_input_2_struct = {
    'data_object': file_struct,
    'to_channel': 'input2'
}

workflow_output_1_struct = {
    'from_channel': 'output1'
}

workflow_struct = {
    'workflow_name': 'workflow1',
    'steps': [step_1_struct, step_2_struct],
    'workflow_inputs': [workflow_input_1_struct, workflow_input_2_struct],
    'workflow_outputs': [workflow_output_1_struct]
    }

workflow_with_templated_command_struct = {
    'workflow_name': 'workflow1',
    'steps': [step_1_struct, step_2_struct],
    'constants': {
        'id': 'workflow123',
        'wf': 'x',
        },
    'workflow_inputs': [workflow_input_1_struct, workflow_input_2_struct],
    'workflow_outputs': [workflow_output_1_struct]
    }

workflow_run_input_struct = {
    'input_name': 'input1',
    'data_object': file_struct
}

workflow_run_struct = {
    'workflow': workflow_struct,
    'workflow_run_inputs': [workflow_run_input_struct]
}
