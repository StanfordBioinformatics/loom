#!/usr/bin/env python
import uuid
import json

sample_id = uuid.uuid4().get_hex()

# Contents of this file are "hello"
hello_file = {
    "hash_function": "md5",
    "hash_value": "b1946ac92492d2347c6235b4d2611184",
}

env = {
    'docker_image': 'ubuntu',
}

world_output_port = {
    'file_path': 'world.txt',
    }

world_step_template = {
    'command': 'echo world > %s' % 'world.txt',
    'environment': env,
    'output_ports': [
        world_output_port,
         ],
}

world_step_definition = {
    'step_template': world_step_template,
    'input_bindings': [],
    }

world_file_recipe = {
    'analysis_definition': world_step_definition,
    'output_port': world_output_port,
    }

hello_input_port = {
    'file_path': 'hello.txt',
    }

world_input_port = {
    'file_path': 'world.txt',
    }

hello_world_output_port = {
    'file_path': 'hello_world.txt',
    }

hello_world_step_template = {
    'command': 'cat %s %s > %s' % ('hello.txt', 'world.txt', 'hello_world.txt'),
    'environment': env,
    'input_ports': [
        hello_input_port,
        world_input_port,
        ],
    'output_ports': [
        hello_world_output_port,
        ],
}

hello_world_step_definition = {
    'step_template': hello_world_step_template,
    'input_bindings':[
        {
            'data_object': world_file_recipe,
            'input_port': world_input_port,
            },
        ]
    }

analysis_request = {
    'analysis_definitions': [hello_world_step_definition],
    'requester': 'someone@example.net',
    }

print json.dumps(analysis_request, indent=2)
