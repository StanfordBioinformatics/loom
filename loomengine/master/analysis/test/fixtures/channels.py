from .data_objects import *


channel_name = 'test_channel'

sender = {'_class': 'WorkflowRunInput'}

receiver = {'_class': 'StepRunInput'}

channel_output = {
    'receiver': receiver,
}

channel = {
    'name': channel_name,
    'outputs': [channel_output],
    'sender': sender,
    'is_closed_to_new_data': False
}
