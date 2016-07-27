from django.test import TestCase
from analysis.serializers.task_definitions import *
from . import fixtures


class TestTaskDefinitionSerializer(TestCase):

    def testTaskDefininitionSerializer(self):
        s = TaskDefinitionSerializer(data=fixtures.task_definitions.task_definition)
        s.is_valid()
        td = s.save()

        self.assertEqual(td.outputs.first().filename,
                         fixtures.task_definitions.task_definition['outputs'][0]['filename'])

    def testTaskDefinitionEnvironmentSerializer(self):
        s = TaskDefinitionEnvironmentSerializer(data=fixtures.task_definitions.task_definition_docker_environment)
        s.is_valid()
        e = s.save()

        self.assertEqual(e.docker_image,
                         fixtures.task_definitions.task_definition_docker_environment['docker_image'])

    def testTaskDefinitionDockerEnvironmentSerializer(self):
        s = TaskDefinitionDockerEnvironmentSerializer(data=fixtures.task_definitions.task_definition_docker_environment)
        s.is_valid()
        e = s.save()

        self.assertEqual(e.docker_image,
                         fixtures.task_definitions.task_definition_docker_environment['docker_image'])

    def testTaskDefinitionInputSerializer(self):
        s = TaskDefinitionInputSerializer(data=fixtures.task_definitions.task_definition_input)
        s.is_valid()
        i = s.save()

        self.assertEqual(i.data_object_content.string_value,
                         fixtures.task_definitions.task_definition_input['data_object_content']['string_value'])

    def testTaskDefinitionOutputSerializer(self):
        s = TaskDefinitionOutputSerializer(data=fixtures.task_definitions.task_definition_output)
        s.is_valid()
        o = s.save()

        self.assertEqual(o.filename, fixtures.task_definitions.task_definition_output['filename'])
