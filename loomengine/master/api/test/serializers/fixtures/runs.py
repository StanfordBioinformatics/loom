#!/usr/bin/env python

from .templates import *

step_run_a = {
    'type': 'step',
    'template': step_a
}

step_run_b = {
    'type': 'step',
    'template': step_b
}

step_run_c = {
    'type': 'step',
    'template': step_c
}

flat_workflow_run = {
    'type': 'workflow',
    'template': flat_workflow
    }

nested_workflow_run = {
    'type': 'workflow',
    'template': nested_workflow
}
