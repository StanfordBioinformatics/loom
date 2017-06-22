from django.test import TestCase

from api.models import *


def get_step_one():
    step_one = Template.objects.create(
        name='step_one',
        command='echo {{one}} > {{two})',
        environment={'docker_image': 'ubuntu'},
        resources={'memory': 6, 'cores': 1},
        inputs=[{'channel': 'one', 'type': 'string',
                 'mode': 'no_scatter', 'group': 0}],
        outputs=[{'channel': 'two', 'type': 'string',
                  'source': {'stream': 'stdout'},
                  'mode': 'no_scatter'}],
        postprocessing_status='complete',
        is_leaf=True)
    return step_one

def get_step_two():
    step_two = Template.objects.create(
        name='step_two',
        command='echo {{two}} "!" > {{three}})',
        environment={'docker_imate': 'ubuntu'},
        resources={'memory': 6, 'cores': 1},
        inputs=[{'channel': 'two', 'type': 'string',
                 'mode': 'no_scatter', 'group': 0}],
        outputs=[{'channel': 'three', 'type': 'string',
                  'source': {'stream': 'stdout'},
                  'mode': 'no_scatter'}],
        postprocessing_status='complete',
        is_leaf=True)
    return step_two
        
def get_workflow():
    workflow = Template.objects.create(
        name='one_two',
        inputs = [{'channel': 'one', 'type': 'string', 'mode': 'no_gather'}],
        outputs = [{'channel': 'three', 'type': 'string'}],
        postprocessing_status='complete',
        is_leaf=False)
    workflow.add_steps([get_step_one(),
                        get_step_two()])
    return workflow



class TestTemplate(TestCase):

    def testCreate(self):

        workflow = get_workflow()

        self.assertEqual(workflow.children.all()[0].child_template.name, 'step_one')
        self.assertEqual(workflow.children.all()[1].child_template.name, 'step_two')
