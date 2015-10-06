import os
import sys
from django.conf import settings
from django.test import TestCase
from analysis.models import Step
from analysis.models.template_helper import StepTemplateHelper
sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.common.fixtures import *

class TestTemplateHelper(TestCase):

    def test_something(self):
        step = Step.create(step_obj_with_templated_command)
        command = StepTemplateHelper(step).render(step.command)
        inputfile = step_obj_with_templated_command['input_ports'][0]['file_path']
        outputfile = step_obj_with_templated_command['output_ports'][0]['file_path']
        self.assertTrue(inputfile in command)
        self.assertTrue(outputfile in command)
