#!/usr/bin/env python
import uuid
import json

sample_id = uuid.uuid4().get_hex()
hello_path = 'hello.txt'
world_path = 'world.txt'
hello_world_path = 'hello_world.txt'
unpunctuated_hello_world_path = 'partialresult.txt'
punctuated_hello_world_path = 'hello_worldfinal.txt'

input_file = {
    "hash_algorithm": "md5",
    "hash_value": "b1946ac92492d2347c6235b4d2611184",
}

env = {
    'docker_image': 'ubuntu',
}

hello_step = {
    'name': 'hello',
    'command': 'echo world > %s' % world_path,
    'environment': env,
}

hello_world_step = {
    'command': 'cat %s %s > %s' % (hello_path, world_path, hello_world_path),
    'environment': env,
    'after': [hello_step['name']],
}

session_1_template = {
    'input_ports': [
        {
            'name': 'input1',
            'local_path': hello_path,
        },
    ],
    'output_ports': [
        {
            'name': 'output1',
            'file_path': hello_world_path,
        }
    ],
    'steps':[
        hello_step,
        hello_world_step,
    ],
}

session_1 = {
    'session_template': session_1_template,
    'input_bindings': [
        {
            'data_object': input_file,
            'input_port': 'input1',
        },
    ],
}

file_recipe_1 = {
    'session': session_1,
    'output_port': 'output1',
}

session_2_template = {
    'input_ports': [
        {
            'name': 'input1',
            'file_path': unpunctuated_hello_world_path,
        }
    ],
    'output_ports': [
        {
            'name': 'output1',
            'file_path': punctuated_hello_world_path,
        }
    ],
    'steps':[
        {
            'command': 'echo "`cat %s`"\! > %s' % (unpunctuated_hello_world_path, punctuated_hello_world_path),
            'environment': env,
        },
    ]
}

session_2 = {
    'session_template': session_2_template,
    'input_bindings': [
        {
            'data_object': file_recipe_1,
            'input_port': 'input1'
        },
    ],
}

file_recipe_2 = {
    'session': session_2,
    'output_port': 'output1',
}

request = {
    'file_recipes': [file_recipe_2],
    'requester': 'somebody@example.net',
}

print json.dumps(request, indent=2)
