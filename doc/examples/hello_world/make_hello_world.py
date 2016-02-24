#!/usr/bin/env python
import uuid
import json

# Contents of this file are "hello"
file_contents = {
    "hash_function": "md5",
    "hash_value": "b1946ac92492d2347c6235b4d2611184",
}

hello_file = {
    'file_contents': file_contents,
    'metadata': '{"filename": "hello.txt"}'
}

env = {
    'docker_image': 'ubuntu',
}

resources = {
    'memory': '1GB',
    'cores': '1',
    }

world_step = {
    'name': 'world_step',
    'command': 'echo world > %s' % 'world.txt',
    'environment': env,
    'resources': resources,
    'output_ports': [
        {
            'name': 'world_out',
            'file_name': 'world.txt',
            }
        ],
}

hello_world_step = {
    'name': 'hello_world_step',
    'command': 'cat %s %s > %s' % ('hello.txt', 'world.txt', 'hello_world.txt'),
    'environment': env,
    'resources': resources,
    'input_ports': [
        {
            'name': 'hello_in',
            'file_name': 'hello.txt',
            },
        {
            'name': 'world_in',
            'file_name': 'world.txt',
            }
        ],
    'output_ports': [
        {
            'name': 'hello_world_out',
            "file_name": "hello_world.txt",
            }
        ],
}

hello_world_workflow = {
    'name': 'hello_world',
    'steps': [
        world_step,
        hello_world_step
        ],
    'data_bindings': [
        {
            'data_object': hello_file,
            'destination': {
                'step': 'hello_world_step',
                'port': 'hello_in',
                }
            }
        ],
    'data_pipes':
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

print json.dumps(hello_world_workflow, separators=(',', ':'), indent=2)