from .data_objects import file_data_object

task_run_input = {
    'data_object': file_data_object
}

task_run_output = {
}

task_run = {
    'inputs': [task_run_input],
    'outputs': [task_run_output],
    'resources': {
        'cores': '1',
        'memory': '1',
        'disk_size': '1024'
    },
}

