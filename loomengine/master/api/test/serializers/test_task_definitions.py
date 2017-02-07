from django.test import TestCase

from api.models import Step, StepRun, TaskRun, TaskDefinition, RequestedDockerEnvironment
from api.serializers.task_definitions import TaskDefinitionSerializer
from api.test import fixtures




class TestTaskDefinition(TestCase):

    def testCreate(self):
        docker_image = 'ubuntu'
        step = Step.objects.create(command='blank')
        environment = RequestedDockerEnvironment.objects.create(docker_image=docker_image, step=step)
        step_run = StepRun.objects.create(template=step)
        task_run = TaskRun.objects.create(step_run=step_run)
        task_definition = TaskDefinition.create_from_task_run(task_run)
        
        s = TaskDefinitionSerializer(task_definition)

        # No values set, but still run the rendering code
        self.assertEqual(s.data['command'], '')
