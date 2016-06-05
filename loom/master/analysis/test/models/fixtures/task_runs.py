from task_definitions import task_definition, task_definition_input, task_definition_output

task_run_input = {
    'task_definition_input': task_definition_input
}

task_run_output = {
    'task_definition_output': task_definition_output
}

task_run = {
    'task_definition': task_definition,
    'task_run_inputs': [task_run_input],
    'task_run_outputs': [task_run_output],
}

