from .data_objects import *
from .workflows import *

run_request_input = {
    'value': 'some text',
    'type': 'string',
    'channel': flat_workflow['inputs'][0]['channel']
}

run_request = {
    'inputs': [
        run_request_input
    ]
}
