from django.test import TestCase

from analysis.test import fixtures
from analysis.serializers.task_definitions import *

class TestTaskDefinition(TestCase):

    def testCreate(self):
        s = TaskDefinitionSerializer(
            data=fixtures.task_definitions.task_definition)
        s.is_valid()
        m = s.save()
        self.assertEqual(m.inputs.first().data_object_content.string_value,
                         fixtures.task_definitions.task_definition\
                         ['inputs'][0]['data_object_content']['string_value'])
                         
