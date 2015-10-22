#!/usr/bin/env python

import json
import os


# Contents of this file are "hello"
file_contents = {
    "hash_function": "md5",
    "hash_value": "b1946ac92492d2347c6235b4d2611184",
}

hello_file = {
    'file_contents': file_contents,
    'metadata': '{"filename": "hello.txt"}'
}

world_file = {
    'file_contents': {
        "hash_function": "md5", 
        "hash_value": "591785b794601e212b260e25925636fd"
        },
    'metadata': '{"filename": "world.txt"}'
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

hello_world_run_request_obj = {
    'workflows': [hello_world_workflow],
    'requester': 'someone@example.net',
    }

world_step_output_port = {
    "file_name": "hello_world.txt",
    "is_array": False,
    }

world_step_definition = {
    'input_ports': [
                      {
                          "file_name": "hello.txt",
                          "data_object": hello_file,
                          "is_array": False,
                          },
                      {
                          "file_name": "world.txt",
                          "data_object": world_file,
                          "is_array": False
                          }
                      ],
    'output_ports': [world_step_output_port],
    'command': world_step['command'],
    'environment': world_step['environment'],
    }

world_step_run = {
    'step_definition': world_step_definition
    }

world_step_result = {
    'step_definition': world_step_definition,
    'data_object': world_file,
    'output_port': world_step_output_port
    }

if __name__=='__main__':
    print json.dumps(hello_world_run_request_obj, separators=(',', ':'), indent=2)
