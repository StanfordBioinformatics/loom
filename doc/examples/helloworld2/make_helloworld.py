#!/usr/bin/env python
import uuid
import json

# Contents of this file are "hello"
hello_file = {
    "hash_function": "md5",
    "hash_value": "b1946ac92492d2347c6235b4d2611184",
}

env = {
    'docker_image': 'ubuntu',
}

world_step = {
    'name': 'world_step',
    'command': 'echo world > %s' % 'world.txt',
    'environment': env,
    'output_ports': [
        {
            'name': 'world_out',
            'file_path': 'world.txt',
            }
        ],
}

hello_world_step = {
    'name': 'hello_world_step',
    'command': 'cat %s %s > %s' % ('hello.txt', 'world.txt', 'hello_world.txt'),
    'environment': env,
    'input_ports': [
        {
            'name': 'hello_in',
            'file_path': 'hello.txt',
            },
        {
            'name': 'world_in',
            'file_path': 'world.txt',
            }
        ],
    'output_ports': [
        {
            'name': 'hello_world_out',
            "file_path": "hello_world.txt",
            }
        ],
}

hello_world_analysis = {
    'steps': [
        world_step,
        hello_world_step
        ],
    'input_bindings': [
        {
            'file': hello_file,
            'destination': {
                'step': 'world_step',
                'port': 'hello_in',
                }
            }
        ],
    'connectors':
        [
        {
            'source': {
                'step': 'world_step',
                'port': 'world_out'
                },
            'destination': {
                'step': 'hello_world_step',
                'port': 'world_in',
                }
            }
        ]
    }

request_run = {
    'analyses': [hello_world_analysis],
    'requester': 'someone@example.net',
    }

print json.dumps(request_run, indent=2)
