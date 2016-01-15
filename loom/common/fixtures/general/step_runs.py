from .data_objects import file_obj
from .workflows import step_1_obj
from .step_definitions import step_definition_obj, step_definition_output_port_obj

# StepRun and related objects

step_result_obj = {
    'output_port': step_definition_output_port_obj,
    'data_object': file_obj,
    }

step_run_minimal_obj = {
    'steps': [step_1_obj],
    }

process_location_obj = {
    'pid': 1234
    }

step_run_input_port = {
    'name': 'input1'
    }

step_run_output_port = {
    'name': 'input2'
    }

step_run_with_everything_obj = {
    'steps': [step_1_obj],
    'step_definition': step_definition_obj,
    'are_results_complete': True,
    'process_location': process_location_obj,
    'input_ports': [step_run_input_port],
    'output_ports': [step_run_output_port]
    }

