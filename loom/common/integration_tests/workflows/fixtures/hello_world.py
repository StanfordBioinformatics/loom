#!/usr/bin/env python

import json
import os

hello_world_workflow_struct = {
        "workflow_outputs": [
            {
                "from_channel": "hello_world_out",
            }
        ],
        "workflow_name": "hello_world",
        "steps": [
            {
                "environment": {
                    "docker_image": "ubuntu"
                },
                "command": "echo world > {{ world }}",
                "step_name": "world_step",
                "resources": {
                    "cores": 1,
                    "memory": "1GB"
                },
                "step_outputs": [
                    {
                        "from_path": "world.txt",
                        "to_channel": "world"
                    }
                ]
            },
            {
                "step_inputs": [
                    {
                        "from_channel": "hello",
                    },
                    {
                        "from_channel": "world",
                    }
                ],
                "environment": {
                    "docker_image": "ubuntu"
                },
                "command": "cat {{ hello }} {{ world }} > {{ hello_world }}",
                "step_name": "hello_world_step",
                "resources": {
                    "cores": 1,
                    "memory": "1GB"
                },
                "step_outputs": [
                    {
                        "from_path": "hello_world.txt",
                        "to_channel": "hello_world_out"
                    }
                ]
            }
        ],
        "workflow_inputs": [
            {
                "type": "file",
                "prompt": "Enter the 'hello' file",
                "input_name": "hello_input",
                "to_channel": "hello"
            }
        ]
    }

hello_world_workflow_run_struct = {
    "workflow_run_inputs": [
        {
            "input_name": "hello_input",
            "data_object": {
                "filename": "hello.txt",
                "file_contents": {
                    "hash_value": "b1946ac92492d2347c6235b4d2611184",
                    "hash_function": "md5"
                }
            }
        }
    ],
    "workflow": hello_world_workflow_struct
}


if __name__=='__main__':
    print json.dumps(hello_world_workflow_run_struct, separators=(',', ':'), indent=2)
