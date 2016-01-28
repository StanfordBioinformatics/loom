from analysis.models.workflows import Step, Workflow
from analysis.models.template_helper import StepTemplateHelper
from django.conf import settings
from django.test import TestCase

import os
import sys
from loom.common.fixtures import *


class FakeDataObject(object):

    def is_array(self):
        return False

class FakeInputSet(object):

    def get_data_object(self):
        return FakeDataObject()

class TestTemplateHelper(TestCase):

    def test_file_name(self):
        step = Step.create(step_with_templated_command_struct)
        command = StepTemplateHelper(step, FakeInputSet()).render(step.command)
        inputfile = step_with_templated_command_struct['input_ports'][0]['file_name']
        outputfile = step_with_templated_command_struct['output_ports'][0]['file_name']
        self.assertTrue(inputfile in command)
        self.assertTrue(outputfile in command)

    def test_substitution(self):
        workflow = Workflow.create(workflow_with_templated_command_struct)
        step = workflow.steps.first()

        step_id = step.constants['id']
        wf_id_overridden = workflow.constants['id']
        wf_const = workflow.constants['wf']

        command = StepTemplateHelper(step, FakeInputSet()).render(step.command)

        self.assertTrue(step_id in command)
        self.assertTrue(wf_id_overridden not in command)
        self.assertTrue(wf_const in command)
        
