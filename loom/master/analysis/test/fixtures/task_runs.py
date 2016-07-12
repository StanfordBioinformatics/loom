from .task_definitions import task_definition, task_definition_input, task_definition_output
from .data_objects import file

task_run_input = {
    'task_definition_input': task_definition_input,
    'data_object': file
}

task_run_output = {
    'task_definition_output': task_definition_output
}

task_run = {
    'task_definition': task_definition,
    'inputs': [task_run_input],
    'outputs': [task_run_output],
    'resources': {
        'cores': '1',
        'memory': '1',
        'disk_space': '1024'
    },
}

