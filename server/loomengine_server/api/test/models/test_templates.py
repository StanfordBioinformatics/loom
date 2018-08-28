from django.test import TestCase

from api.models import *
from api.test.models import _get_string_data_node

def get_step_one():
    step_one = Template.objects.create(
        name='step_one',
        command='echo {{one}} > {{two})',
        environment={'docker_image': 'ubuntu'},
        resources={'memory': "6", 'cores': "1"},
        outputs=[{'channel': 'two', 'type': 'string',
                  'source': {'stream': 'stdout'},
                  'mode': 'no_scatter'}],
        is_leaf=True)
    TemplateInput.objects.create(
        channel='one',
        type='string',
        mode='no_scatter',
        group=0,
        template=step_one)
    return step_one

def get_step_two():
    step_two = Template.objects.create(
        name='step_two',
        command='echo {{two}} "!" > {{three}})',
        environment={'docker_image': 'ubuntu'},
        resources={'memory': 6, 'cores': 1},
        outputs=[{'channel': 'three', 'type': 'string',
                  'source': {'stream': 'stdout'},
                  'mode': 'no_scatter'}],
        is_leaf=True)
    TemplateInput.objects.create(
        channel='two',
        type='string',
        mode='no_scatter',
        group=0,
        template=step_two)
    return step_two
        
def get_template():
    template = Template.objects.create(
        name='one_two',
        outputs = [{'channel': 'three', 'type': 'string'}],
        is_leaf=False)
    default = _get_string_data_node('default data')
    TemplateInput.objects.create(
        channel='one',
        type='string',
        mode='no_gather',
        data_node=default,
        template=template)
    template.add_steps([get_step_one(),
                        get_step_two()])
    return template


class TestTemplate(TestCase):

    def testCreate(self):

        template = get_template()

        self.assertEqual(template.steps.all()[0].name, 'step_one')
        self.assertEqual(template.steps.all()[1].name, 'step_two')
