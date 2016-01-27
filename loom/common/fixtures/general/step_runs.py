from .data_objects import file_struct
from .workflows import step_1_struct
from .step_definitions import step_definition_struct, step_definition_output_port_struct

# StepRun and related models

step_result_struct = {
    'output_port': step_definition_output_port_struct,
    'data_object': file_struct,
    }

step_run_minimal_struct = {
    'steps': [step_1_struct],
    }

process_location_struct = {
    'pid': 1234
    }

step_run_input_port = {
    'name': 'input1'
    }

step_run_output_port = {
    'name': 'input2'
    }

step_run_with_everything_struct = {
    'steps': [step_1_struct],
    'step_definition': step_definition_struct,
    'are_results_complete': True,
    'process_location': process_location_struct,
    'input_ports': [step_run_input_port],
    'output_ports': [step_run_output_port]
    }

