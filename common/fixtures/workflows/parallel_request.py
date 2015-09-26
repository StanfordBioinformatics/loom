#!/usr/bin/env python
import uuid
import json


def _make_parallel_request():
    env = {
        'docker_image': 'ubuntu',
        }
    
    resources = {
        'memory': '1GB',
        'cores': '1',
        }
    
    create_text_step = {
        'name': 'create_text_step',
        'command': 'echo hello > {{ output.text_file }}',
        'environment': env,
        'resources': resources,
        'output_ports': [
            {
                'name': 'text_file',
                'data_type': 'file',
                'file_name': 'text.txt'
                }
            ]
        }
    
    split_step = {
        'name': 'split_step',
        'command': 'cat {{ input.text_file }} > out1.txt; cat {{ input.hello }} > out1.txt;',
        'environment': env,
        'resources': resources,
        'input_ports': [
            {
                'data_type': 'file',
                'name': 'text_file',
                'file_name': 'text.txt',
                }
            ],
        'output_ports': [
            {
                'data_type': 'file_array',
                'name': 'text_file_array',
                'glob': 'out*.txt',
                }
            ]
        }
    
    merge_step = {
        'name': 'merge_step',
        'command': 'cat {% for f in input.text_file_array %}{{f}} {% endfor%} > {{ output.text_file }}',
        'environment': env,
        'resources': resources,
        'input_ports': [
            {
                'name': 'text_file_array',
                'data_type': 'file_array',
                'file_name': 'text_{{ i }}.txt'
                }
            ],
        'output_ports': [
            {
                'name': 'text_file',
                'file_name': 'out.txt',
                'data_type': 'file',
                }
            ]
        }
    
    split_merge_workflow = {
        'name': 'split_merge',
        'steps': [
            create_text_step,
            split_step,
            merge_step,
            ],
        'data_pipes':
            [
            {
                'source': {
                    'step': 'create_text_step',
                    'port': 'text_file'
                    },
                'destination': {
                    'step': 'split_step',
                    'port': 'text_file',
                    }
                },
            {
                'source': {
                    'step': 'split_step',
                    'port': 'text_file_array',
                    },
                'destination': {
                    'step': 'merge_step',
                    'port': 'text_file_array',
                    }
                }
            ]
        }
    
    request_run = {
        'workflows': [split_merge_workflow],
        'requester': 'someone@example.net',
        }

    return request_run

parallel_request = _make_parallel_request()

if __name__=='__main__':
    print json.dumps(parallel_request, indent=2)
