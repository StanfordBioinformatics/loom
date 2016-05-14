from .data_objects import *

channel_name = 'test_channel'

source_node = {
    'channel_name': channel_name
}

destination_node = {
    'channel_name': channel_name
}

channel_output_struct = {
    'data_objects': [file_struct],
    'receiver': destination_node,
}

channel_struct = {
    'channel_name': channel_name,
    'channel_outputs': [channel_output_struct],
    'sender': source_node,
    'is_closed_to_new_data': False
}
