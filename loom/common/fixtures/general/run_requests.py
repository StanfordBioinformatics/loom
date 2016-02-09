from .data_objects import file_struct

# WorkflowRunRequest and related objects

resource_set_struct = {
    'memory': '5G',
    'cores': 4,
    }

docker_image_struct = {
    'docker_image': '1234567asdf',
    }

step_run_request_1_struct = {
    'name': 'step1',
    'command': 'echo hello',
    'environment': docker_image_struct,
    'resources': resource_set_struct,
    }

step_run_request_2_struct = {
    'name': 'step2',
    'command': 'echo world',
    'environment': docker_image_struct,
    'resources': resource_set_struct,
    }

workflow_run_request_struct = {
    'step_run_requests': [step_run_request_1_struct, step_run_request_2_struct],
    }

workflow_run_request_with_templated_command_struct = {
    'step_run_requests': [step_run_request_1_struct, step_run_request_2_struct],
    'constants': {
        'id': 'workflow123',
        'wf': 'x',
        }
    }
