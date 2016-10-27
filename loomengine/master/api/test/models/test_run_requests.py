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
        RequestedDockerEnvironment.objects.create(step=step_one, docker_image='ubuntu')
        RequestedResourceSet.objects.create(step=step_one, memory=6, cores=1)
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
        source = StepOutputSource.objects.create(stream='stdout', step_output=output_three)
        
        step_two = Step.objects.create(name='step_two',
                                       command='echo {{three}} "!" > {{four}})',
                                       parent_workflow=workflow)
        RequestedDockerEnvironment.objects.create(step=step_two, docker_image='ubuntu')
        RequestedResourceSet.objects.create(step=step_two, memory=6, cores=1)

        input_three = StepInput.objects.create(
            step=step_two, channel='three', type='string')
        output_four = StepOutput.objects.create(
            step=step_two, channel='four', type='string')
        source = StepOutputSource.objects.create(stream='stdout', step_output=output_four)
        return workflow

    def _get_run_request(self):
        template = self._get_template()
        run_request = RunRequest.objects.create(template=template)
        input_one = RunRequestInput.objects.create(
            run_request=run_request, channel='one')
        input_one.add_data_objects_from_json("one", 'string')
        run_request.initialize()
        return run_request

    def testInitialize(self):
        run_request = self._get_run_request()

        # Verify that input data to run_request is shared with input node for step
        step_one = run_request.run.step_runs.all().get(
            steprun__template__name='step_one')
        data = step_one.inputs.first().data
        self.assertEqual(data, '"one"')

    def testStartReadyTasks(self):
        run_request = self._get_run_request()
        run_request.initialize()

        # This should create a task run for the first step
        run_request.create_ready_tasks(do_start=False)

        step_one = run_request.run.step_runs.all().get(
            steprun__template__name='step_one')

        self.assertEqual(step_one.task_runs.count(), 1)
