import os

with open(os.path.join(
        os.path.dirname(__file__),
        '../../doc/examples/helloworld/helloworld.json'
        )) as f:
    helloworld_json = f.read()


hello_world_step_definition_obj1 = {
    "template":
        {
        "command":"echo world > world.txt",
        "environment": {
            "docker_image":"ubuntu"
            },
        "output_ports": [
            {
                "file_path": "world.txt"
                }
            ]
        }
    }

hello_world_step_run_obj1 = {
    "output_binding": {
        "file": {
            "hash_function":"md5",
            "hash_value":"8c2753548775b4161e531c323ea24c08"
            },
        "output_port": {
            "file_path": "world.txt"
            }
        },
    "step_definition": hello_world_step_definition_obj1,
    }

hello_world_step_result_obj1 = {
    'step_definition': hello_world_step_definition_obj1,
    'output_binding': {
        'output_port': {
            'file_path': u'world.txt',
            }, 
        'data_object': {
            'file_contents': {
                'hash_value': u'8c2753548775b4161e531c323ea24c08', 
                'hash_function': u'md5'
                }
            }
        }
    }

hello_world_step_definition_obj2 = {
    'data_bindings': [
        {
            'input_port': {
                'file_path': u'hello.txt'
                }, 
            'data_object': {
                'file_contents': {
                    'hash_value': u'b1946ac92492d2347c6235b4d2611184', 
                    'hash_function': u'md5'
                    }
                }
            }
        ], 
    'template': {
        'environment': {
            'docker_image': u'ubuntu'
            }, 
        'input_ports': [
            {
                'file_path': u'hello.txt'
                }, 
            {
                'file_path': u'world.txt'
                }
            ], 
        'command': u'cat hello.txt world.txt > hello_world.txt', 
        'output_ports': [
            {
                'file_path': u'hello_world.txt'
                }
            ]
        }
    }

hello_world_step_result_obj2 = {
    'step_definition': hello_world_step_definition_obj2,
    'output_binding': {
        'output_port': {
            'file_path': u'hello_world.txt'
            }, 
        'data_object': {
            'file_contents': {
                'hash_value': u'ffdc12d8d601ae40f258acf3d6e7e1fb', 
                'hash_function': u'md5'
                }
            }
        }
    }

hello_world_step_run_obj1 = {
    "is_complete": True,
    "step_definition": hello_world_step_definition_obj1,
    "step_results": [
        hello_world_step_result_obj1,
        ]
    }

hello_world_step_run_obj2 = {
    'step_definition': hello_world_step_definition_obj2,
    'is_complete': True, 
    'step_results': [hello_world_step_result_obj2]
    }

hello_world_request_with_runs = {
    'workflows': [
        {
            'data_pipes': [
                {'source': {
                        'step': 'world_step', 
                        'port': 'world_out'
                        }, 
                 'destination': {
                        'step': 'hello_world_step', 
                        'port': 'world_in'
                        }
                 }], 
            'steps': [
                {
                    'environment': {
                        'docker_image': 'ubuntu'
                        }, 
                    'command': 'echo world > world.txt', 
                    'name': 'world_step', 
                    'resources': {
                        'cores': '1', 
                        'memory': '5GB'
                        }, 
                    'output_ports': [
                        {
                            'name': 'world_out', 'file_path': 'world.txt'
                            }
                        ],
                    'step_run': hello_world_step_run_obj1,
                    }, 
                {
                    'name': 'hello_world_step', 
                    'input_ports': [
                        {
                            'name': 'hello_in', 
                            'file_path': 'hello.txt'
                            }, 
                        {
                            'name': 'world_in', 
                            'file_path': 'world.txt'
                            }
                        ], 
                    'environment': {
                        'docker_image': 'ubuntu'
                        }, 
                    'command': 'cat hello.txt world.txt > hello_world.txt', 
                    'output_ports': [
                        {
                            'name': 'hello_world_out', 
                            'file_path': 'hello_world.txt'
                            }
                        ], 
                    'resources': {
                        'cores': '1', 
                        'memory': '5GB'
                        },
                    'step_run': hello_world_step_run_obj2,
                    }
                ], 
         'data_bindings': [
                {
                    'destination': {
                        'step': 'hello_world_step', 
                        'port': 'hello_in'
                        }, 
                    'data_object': {
                        'file_contents': {
                            'hash_value': 'b1946ac92492d2347c6235b4d2611184', 
                            'hash_function': 'md5'
                            }
                        }
                    }
                ]
         }
        ], 
    'requester': u'someone@example.net'
    }

file_contents_obj = {
    'hash_value': '1234asfd',
    'hash_function': 'md5', 
    }

file_obj = {
    'file_contents': file_contents_obj,
    }

file_contents_obj_2 = {
    'hash_value': 'xyz123',
    'hash_function': 'md5',
    }

file_obj_2 = {
    'file_contents': file_contents_obj_2,
    }

file_array_obj = {
    'files': [
        file_obj,
        file_obj_2
        ]
    }

server_file_storage_location_obj = {
    'file_contents': file_contents_obj,
    'file_path': '/absolute/path/to/my/file.txt',
    'host_url': 'localhost',
    }

server_file_storage_location_obj_2 = {
    'file_contents': file_contents_obj_2,
    'file_path': '/absolute/path/to/my/file2.txt',
    'host_url': 'localhost',
    }

file_import_request_obj = {
    'file_storage_location': server_file_storage_location_obj,
    'comments': "Description of file source",
    'requester': "someone@somewhere.net",
    }

docker_image_obj = {
    'docker_image': '1234567asdf',
    }

step_definition_input_port_obj = {
    'name': 'input1',
    'file_path':'copy/my/file/here.txt',
    }

step_definition_output_port_obj = {
    'name': 'output1',
    'file_path':'look/for/my/file/here.txt',
    }

step_definition_data_binding_obj = {
    'data_object': file_obj,
    'input_port': step_definition_input_port_obj,
    }

template_obj = {
    'input_ports': [step_definition_input_port_obj],
    'output_ports': [step_definition_output_port_obj],
    'command': 'echo test',
    'environment': docker_image_obj,
    }

step_definition_obj = {
    'template': template_obj,
    'data_bindings': [step_definition_data_binding_obj],
    }

docker_image_obj = {
    'docker_image': 'ubuntu',
    }

input_port_obj_1 = {
    'name': 'input_port1',
    'file_path': 'rel/path/to/input_file',
    }

output_port_obj_1 = {
    'name': 'output_port1',
    'file_path': 'rel/path/to/output_file',
    }

input_port_obj_2 = {
    'name': 'input_port2',
    'file_path': 'rel/path/to/input_file',
    }

output_port_obj_2 = {
    'name': 'output_port2',
    'file_path': 'rel/path/to/output_file',
    }

port_identifier_obj = {
    'step': 'stepname',
    'port': 'portname',
    }

data_binding_obj = {
    'data_object': file_obj,
    'destination': {
        'step': 'step1',
        'port': 'input_port1',
        },
    }

data_pipe_obj = {
    'source': {
        'step': 'step1',
        'port': 'output_port1',
        },
    'destination': {
        'step': 'step2',
        'port': 'input_port2',
        },
    }

resource_set_obj = {
    'memory': '5G',
    'cores': 4,
    }

step_obj_1 = {
    'name': 'step1',
    'input_ports': [input_port_obj_1],
    'output_ports': [output_port_obj_1],
    'command': 'echo hello',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }

step_obj_2 = {
    'name': 'step2',
    'input_ports': [input_port_obj_2],
    'output_ports': [output_port_obj_2],
    'command': 'echo world',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }

step_obj_with_templated_command = {
    'name': 'step1',
    'input_ports': [input_port_obj_1],
    'output_ports': [output_port_obj_1],
    'command': 'echo {{ input_ports.input_port1.file_path }} > {{ output_ports.output_port1.file_path }}',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }


workflow_obj = {
    'steps': [step_obj_1, step_obj_2],
    'data_bindings': [data_binding_obj],
    'data_pipes': [data_pipe_obj],
    }

request_submission_obj = {
    'workflows': [workflow_obj],
    'requester': 'someone@example.com',
    }

