from .data_objects import file_struct

# WorkflowRunRequest and related objects

resource_set_struct = {
    'memory': '5G',
    'cores': 4,
    }

docker_environment_struct = {
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
    'environment': docker_environment_struct,
    'resources': resource_set_struct,
    'step_inputs': [step_input_1_struct],
    'step_outputs': [step_output_1_struct]
    }

step_2_struct = {
    'step_name': 'step2',
    'command': 'echo world',
    'environment': docker_environment_struct,
    'resources': resource_set_struct,
    'step_inputs': [step_input_2_struct],
    'step_outputs': [step_output_2_struct]
    }

workflow_input_1_struct = {
    'type': 'string',
    'value': 'hey',
    'to_channel': 'input1'
}

workflow_input_2_struct = {
    'type': 'string',
    'value': 'there',
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


straight_pipe_workflow_struct = {
    "workflow_name": "straight_pipe",
    "workflow_inputs": [
	{
	    "type": "file",
	    "value": "one.txt@c4f3f632b7b503149f88d9de9f9bd0927a066ee935fdc011a75ff4a216d6e061",
	    "to_channel": "one_txt"
	}
    ],
    "workflow_outputs": [
	{
	    "from_channel": "result"
	}
    ],
    "steps": [
        {
            "step_name": "step_a",
            "command": "cat {{ one_txt }} {{ one_txt }} > {{ two_txt }}",
            "environment": {
                "docker_image": "ubuntu"
            },
            "resources": {
                "cores": 1,
                "memory": "1GB"
            },
	    "step_inputs": [
		{
		    "from_channel": "one_txt"
		}
	    ],
	    "step_outputs": [
		{
                    "from_path": "two.txt",
		    "to_channel": "two_txt"
		}
            ]
        },
        {
            "step_name": "step_b",
            "command": "cat {{ two_txt }} {{ two_txt }} > {{ result }}",
            "environment": {
                "docker_image": "ubuntu"
            },
	    "resources": {
                "cores": 1,
                "memory": "1GB"
            },
            "step_inputs": [
		{
		    "from_channel": "two_txt"
		}
            ],
            "step_outputs": [
		{
                    "from_path": "result.txt",
		    "to_channel": "result"
		}
            ]
        }
    ]
}

straight_pipe_workflow_input_file_struct = {
    'filename': 'one.txt',
    'file_contents': {
        'hash_value': '0f4265386f51c0b54c6ee36dc1ec0418',
        'hash_function': 'md5'
    }
}
