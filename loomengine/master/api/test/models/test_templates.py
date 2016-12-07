from django.test import TestCase

from api.models import *

class TestTemplate(TestCase):

    def _get_step_one(self):
        step_one = Step.objects.create(
            name='step_one',
            command='echo {{one}} > {{two})',
            environment={'docker_image': 'ubuntu'},
            resources={'memory': 6, 'cores': 1},
            inputs=[{'channel': 'one', 'type': 'string'}],
            outputs=[{'channel': 'two', 'type': 'string',
                      'source': {'stream': 'stdout'}}])
        return step_one

    def _get_step_two(self):
        step_two = Step.objects.create(
            name='step_two',
            command='echo {{two}} "!" > {{three}})',
            environment={'docker_imate': 'ubuntu'},
            resources={'memory': 6, 'cores': 1},
            inputs=[{'channel': 'two', 'type': 'string'}],
            outputs=[{'channel': 'three', 'type': 'string',
                      'source': {'stream': 'stdout'}}]
        )
        return step_two
        
    def _get_workflow(self):
        workflow = Workflow.objects.create(
            type='workflow',
            name='one_two',
            inputs = [{'channel': 'one', 'type': 'string'}],
            outputs = [{'channel': 'three', 'type': 'string'}]
        )
        workflow.add_steps([self._get_step_one(),
                            self._get_step_two()])
        return workflow

    def testCreate(self):

        workflow = self._get_workflow()

        self.assertEqual(workflow.children.all()[0].child_template.name, 'step_one')
        self.assertEqual(workflow.children.all()[1].child_template.name, 'step_two')

    def testGetInputType(self):
        workflow = self._get_workflow()
        input_one_type = workflow.get_input_type('one')
        self.assertEqual(input_one_type, 'string')
