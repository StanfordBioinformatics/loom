from .data_objects import *
from .workflows import *

run_request_input = {
    'value': 'some text',
    'channel': flat_workflow['inputs'][0]['channel']
}

flat_run_request = {
    'template': flat_workflow,
    'inputs': [
        run_request_input
    ]
}

nested_run_request = {
    'template': nested_workflow,
}
