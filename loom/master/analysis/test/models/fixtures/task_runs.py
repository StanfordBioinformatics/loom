from task_definitions import task_definition_struct, task_definition_input_struct, task_definition_output_struct

task_run_input = {
    'task_definition_input': task_definition_input_struct
}

task_run_output = {
    'task_definition_output': task_definition_output_struct
}

task_run_struct = {
    'task_definition': task_definition_struct,
    'task_run_inputs': [task_run_input],
    'task_run_outputs': [task_run_output],
}

