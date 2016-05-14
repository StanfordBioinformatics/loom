#!/usr/bin/env python

import copy
from .workflows import *

step_run_a_struct = {
    'inputs': [
        {
            'channel_name': step_a_struct['inputs'][0]['channel']
        },
        {
            'channel_name': step_a_struct['fixed_inputs'][0]['channel']
        }
    ],
    'outputs': [{
        'channel_name': step_a_struct['outputs'][0]['channel']
    }],
    'template_step': step_a_struct
}

step_run_b_struct = {
    'inputs': [
        {
            'channel_name': step_b_struct['inputs'][0]['channel']
        },
        {
            'channel_name': step_b_struct['inputs'][1]['channel']
        },
        {
            'channel_name': step_b_struct['fixed_inputs'][0]['channel']
        }
    ],
    'outputs': [{
        'channel_name': step_b_struct['outputs'][0]['channel']
    }],
    'template_step': step_b_struct
}

step_run_c_struct = {
    'inputs': [
        {
            'channel_name': step_c_struct['inputs'][0]['channel']
        }
    ],
    'outputs': [{
        'channel_name': step_c_struct['outputs'][0]['channel']
    }],
    'template_step': step_c_struct
}

flat_workflow_run_struct = {
    'step_runs': [
        step_run_a_struct,
        step_run_b_struct
    ],
    'inputs': [
	{
	    'channel_name': flat_workflow_struct['inputs'][0]['channel']
	},
	{
	    'channel_name': flat_workflow_struct['fixed_inputs'][0]['channel']
	}
    ],
    'outputs': [
        {
            'channel_name': flat_workflow_struct['outputs'][0]['channel']
        }
    ],
    'template_workflow': flat_workflow_struct
    }

nested_workflow_run_struct = {
    'step_runs': [
        flat_workflow_run_struct,
        step_run_c_struct
    ],
    'inputs': [
    	{
	    'channel_name': nested_workflow_struct['fixed_inputs'][0]['channel']
	}
    ],
    'outputs': [
    	{
	    'channel_name': nested_workflow_struct['outputs'][0]['channel']
	}
    ],
    'template_workflow': nested_workflow_struct
}

