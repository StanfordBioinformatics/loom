from .data_objects import *
from .workflows import *

run_request_input = {
    'id': 'input.txt@9a6a9c9074509fbff3a65e819bb7eb7f',
    'channel': flat_workflow_struct['inputs'][0]['channel']
}

run_request = {
    'workflow': flat_workflow_struct,
    'inputs': [
        run_request_input
    ]
}
