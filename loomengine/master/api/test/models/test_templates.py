from django.test import TestCase

from api.models import *

class TestTemplate(TestCase):

    def _get_step_one(self):
        step_one = Step.objects.create(name='step_one',
                                       command='echo {{one}} {{two}} > three)')
        StepEnvironment.objects.create(step=step_one,
                                                  docker_image='ubuntu')
        StepResourceSet.objects.create(step=step_one, memory=6, cores=1)
        input_one = StepInput.objects.create(
            step=step_one, channel='one', type='string')
        data_object = StringDataObject.objects.create(
            type='string',
            value='two'
        )
        input_two = FixedStepInput.objects.create(
            step=step_one, channel='two', type='string', data_object=data_object)
        output_three = StepOutput.objects.create(
            step=step_one, channel='three', type='string')
        source = StepOutputSource.objects.create(
            stream='stdout', output=output_three)
        step_one.validate()
        return step_one

    def _get_step_two(self):
        step_two = Step.objects.create(name='step_two',
                                       command='echo {{three}} "!" > {{four}})')
        StepEnvironment.objects.create(step=step_two,
                                                  docker_image='ubuntu')
        StepResourceSet.objects.create(step=step_two, memory=6, cores=1)

        input_three = StepInput.objects.create(
            step=step_two, channel='three', type='string')
        output_four = StepOutput.objects.create(
            step=step_two, channel='four', type='string')
        source = StepOutputSource.objects.create(stream='stdout',
                                                 output=output_four)
        step_two.validate()
        return step_two
        
    def _get_workflow(self):
        workflow = Workflow.objects.create(type='workflow',
                                           name='one_two')
        wf_input_one = WorkflowInput.objects.create(
            workflow=workflow, channel='one', type='string')
        wf_output_four = WorkflowOutput.objects.create(
            workflow=workflow, channel='four', type='string')
        workflow.add_steps([self._get_step_one(),
                            self._get_step_two()])
        workflow.validate()
        return workflow

    def testCreate(self):

        workflow = self._get_workflow()

        self.assertEqual(workflow.children.all()[0].child_template.name, 'step_one')
        self.assertEqual(workflow.children.all()[1].child_template.name, 'step_two')
