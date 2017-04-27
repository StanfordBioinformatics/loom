from .data_objects import *
from .templates import *

run_request_input = {
    'data': {'contents': 'some text'},
    'type': 'string',
    'channel': flat_workflow['inputs'][0]['channel']
}

run_request_parallel_inputs = {
    'data': {'contents': ['some', 'text']},
    'type': 'string',
    'channel': flat_workflow['inputs'][0]['channel']
}
