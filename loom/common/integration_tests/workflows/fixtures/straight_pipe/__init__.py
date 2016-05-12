import json
import os

with open(os.path.join(
        os.path.dirname(__file__),
        'straight_pipe.json')
) as f:
    straight_pipe_workflow_struct = json.load(f)

straight_pipe_workflow_input_file_struct = {
    'filename': 'one.txt',
    'file_contents': {
        'hash_value': '0f4265386f51c0b54c6ee36dc1ec0418',
        'hash_function': 'md5'
    }
}
