import os
import sys
from django.conf import settings
from django.test import TestCase
from analysis.models import Step, RequestSubmission
from analysis.models.template_helper import StepTemplateHelper
sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from loom.common.fixtures import *

class TestTemplateHelper(TestCase):

    def test_file_path(self):
        step = Step.create(step_obj_with_templated_command)
        command = StepTemplateHelper(step).render(step.command)
        inputfile = step_obj_with_templated_command['input_ports'][0]['file_path']
        outputfile = step_obj_with_templated_command['output_ports'][0]['file_path']
        self.assertTrue(inputfile in command)
        self.assertTrue(outputfile in command)

    def test_substitution(self):
        request_submission = RequestSubmission.create(request_submission_obj_with_templated_command)
        workflow = request_submission.workflows.first()
        step = workflow.steps.first()

        step_id = step.constants['id']
        rs_id_overridden = request_submission.constants['id']
        rs_const = request_submission.constants['rs']
        wf_const = workflow.constants['wf']

        command = StepTemplateHelper(step).render(step.command)

        self.assertTrue(step_id in command)
        self.assertTrue(rs_id_overridden not in command)
        self.assertTrue(rs_const in command)
        self.assertTrue(wf_const in command)
        
