from analysis.models.run_requests import Step, RunRequest
from analysis.models.template_helper import StepTemplateHelper
from django.conf import settings
from django.test import TestCase

import os
import sys
from loom.common.fixtures import *


class TestTemplateHelper(TestCase):

    def test_file_name(self):
        step = Step.create(step_with_templated_command_obj)
        command = StepTemplateHelper(step).render(step.command)
        inputfile = step_with_templated_command_obj['input_ports'][0]['file_name']
        outputfile = step_with_templated_command_obj['output_ports'][0]['file_name']
        self.assertTrue(inputfile in command)
        self.assertTrue(outputfile in command)

    def test_substitution(self):
        run_request = RunRequest.create(run_request_with_templated_command_obj)
        workflow = run_request.workflows.first()
        step = workflow.steps.first()

        step_id = step.constants['id']
        rs_id_overridden = run_request.constants['id']
        rs_const = run_request.constants['rs']
        wf_const = workflow.constants['wf']

        command = StepTemplateHelper(step).render(step.command)

        self.assertTrue(step_id in command)
        self.assertTrue(rs_id_overridden not in command)
        self.assertTrue(rs_const in command)
        self.assertTrue(wf_const in command)
        
