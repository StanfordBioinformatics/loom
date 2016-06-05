#!/usr/bin/env python

import copy
from .workflows import *

step_run_a = {
    'inputs': [
        {
            'channel_name': step_a['inputs'][0]['channel']
        },
        {
            'channel_name': step_a['fixed_inputs'][0]['channel']
        }
    ],
    'outputs': [{
        'channel_name': step_a['outputs'][0]['channel']
    }],
    'template_step': step_a
}

step_run_b = {
    'inputs': [
        {
            'channel_name': step_b['inputs'][0]['channel']
        },
        {
            'channel_name': step_b['inputs'][1]['channel']
        },
        {
            'channel_name': step_b['fixed_inputs'][0]['channel']
        }
    ],
    'outputs': [{
        'channel_name': step_b['outputs'][0]['channel']
    }],
    'template_step': step_b
}

step_run_c = {
    'inputs': [
        {
            'channel_name': step_c['inputs'][0]['channel']
        }
    ],
    'outputs': [{
        'channel_name': step_c['outputs'][0]['channel']
    }],
    'template_step': step_c
}

flat_workflow_run = {
    'step_runs': [
        step_run_a,
        step_run_b
    ],
    'inputs': [
	{
	    'channel_name': flat_workflow['inputs'][0]['channel']
	},
	{
	    'channel_name': flat_workflow['fixed_inputs'][0]['channel']
	}
    ],
    'outputs': [
        {
            'channel_name': flat_workflow['outputs'][0]['channel']
        }
    ],
    'template_workflow': flat_workflow
    }

nested_workflow_run = {
    'step_runs': [
        flat_workflow_run,
        step_run_c
    ],
    'inputs': [
    	{
	    'channel_name': nested_workflow['fixed_inputs'][0]['channel']
	}
    ],
    'outputs': [
    	{
	    'channel_name': nested_workflow['outputs'][0]['channel']
	}
    ],
    'template_workflow': nested_workflow
}

