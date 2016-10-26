from django.test import TestCase

from api.models import *

class TestRunRequest(TestCase):
    def _get_template(self):
        workflow = Workflow.objects.create(name='one_two')
        wf_input_one = WorkflowInput.objects.create(
            workflow=workflow, channel='one', type='string')
        wf_output_four = WorkflowOutput.objects.create(
            workflow=workflow, channel='four', type='string')

        step_one = Step.objects.create(name='step_one',
                                       command='echo {{one}} {{two}} > {{three}})',
                                       parent_workflow=workflow)
        input_one = StepInput.objects.create(
            step=step_one, channel='one', type='string')
        data_object = StringDataObject.objects.create(
            string_content=StringContent.objects.create(
                string_value='two'
            )
        )
        input_two = FixedStepInput.objects.create(
            step=step_one, channel='two', type='string', data_object=data_object)
        output_three = StepOutput.objects.create(
            step=step_one, channel='three', type='string')

        step_two = Step.objects.create(name='step_two',
                                       command='echo {{three}} "!" > {{four}})',
                                       parent_workflow=workflow)
        input_three = StepInput.objects.create(
            step=step_two, channel='three', type='string')
        output_four = StepOutput.objects.create(
            step=step_two, channel='four', type='string')
        return workflow

    def _get_uninitialized_run_request(self):
        template = self._get_template()
        run_request = RunRequest.objects.create(template=template)
        input_one = RunRequestInput.objects.create(
            run_request=run_request, channel='one')
        input_one.add_data_objects_from_json("one", 'string')
        return run_request

    def testInitialize(self):
        # After creating a skeleton request with just a template and inputs,
        # idempotent_initialize should create the run
        run_request = self._get_uninitialized_run_request()
        run_request._initialize()
        run_request._connect_channels()

        # Verify that input data to run_request is shared with input node for step
        data = StepRun.objects.get(template__name='step_one').inputs.first().data
        self.assertEqual(data, '"one"')
