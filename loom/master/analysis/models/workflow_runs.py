from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import DataObject
from universalmodels import fields


"""
This module defines WorkflowRun and other classes related to
receiving and running a request for analysis.
"""


class WorkflowRun(AnalysisAppInstanceModel):
    """WorkflowRun represents a request to execute a Workflow on a particular
    set of inputs, and the execution status of that Workflow
    """

    NAME_FIELD = 'workflow__workflow_name'
    
    workflow = fields.ForeignKey('Workflow')
    workflow_run_inputs = fields.OneToManyField('WorkflowRunInput')
    workflow_run_outputs = fields.OneToManyField('WorkflowRunOutput')
    step_runs = fields.OneToManyField('StepRun')
    channels = fields.OneToManyField('Channel')
    status = fields.CharField(
        max_length=255,
        default='running',
        choices=(('running', 'Running'),
                 ('error', 'Error'),
                 ('canceled', 'Canceled'),
                 ('complete', 'Complete')
        )
    )
    status_message = fields.CharField(
        max_length=1000,
        default='Workflow is running'
    )

    @classmethod
    def update_and_run_all(cls):
        for workflow_run in cls.objects.filter(status='running'):
            workflow_run.update_and_run()

    def update_and_run(self):
        for step_run in self.step_runs.filter(status='waiting') | self.step_runs.filter(status='running'):
            step_run.update_and_run()
    
    @classmethod
    def order_by_most_recent(cls, count=None):
        workflow_runs = cls.objects.order_by('datetime_created').reverse()
        if count is not None and (workflow_runs.count() > count):
            return workflow_runs[:count]
        else:
            return workflow_runs

    @classmethod
    def create(cls, *args, **kwargs):
        workflow_run = super(WorkflowRun, cls).create(*args, **kwargs)
        workflow_run._create_inputs_and_outputs()
        workflow_run._create_step_runs()
        workflow_run._create_channels()
        # TODO Assign workflow status (probably w/ default field)
        return workflow_run

    def _create_inputs_and_outputs(self):
        for workflow_input in self.workflow.workflow_inputs.all():
            self._create_workflow_run_input(workflow_input)
        for workflow_output in self.workflow.workflow_outputs.all():
            self._create_workflow_run_output(workflow_output)

    def _create_workflow_run_input(self, workflow_input):
        self.workflow_run_inputs.add(
            WorkflowRunInput.create(
                {'workflow_input': workflow_input.to_struct()}
            )
        )

    def _create_workflow_run_output(self, workflow_output):
        self.workflow_run_outputs.add(
            WorkflowRunOutput.create(
                {'workflow_output': workflow_output.to_struct()}
            )
        )

    def _create_step_runs(self):
        for step in self.workflow.steps.all():
            self._create_step_run(step)

    def _create_step_run(self, step):
        step_run = StepRun.create(
            {'step': step.to_struct()}
        )
        self.step_runs.add(step_run)
        for step_input in step_run.step.step_inputs.all():
            step_run.step_run_inputs.add(
                StepRunInput.create(
                    {'step_input': step_input.to_struct()}
                ))
        for step_output in step_run.step.step_outputs.all():
            step_run.step_run_outputs.add(
                StepRunOutput.create(
                    {'step_output': step_output.to_struct()}
                )
            )
    
    def _create_channels(self):
        # One per workflow_run_input and one per step_run_output
        for workflow_run_input in self.workflow_run_inputs.all():
            channel_name = workflow_run_input.workflow_input.to_channel
            self._add_channel(workflow_run_input, channel_name)
        for step_run in self.steps_runs.all():
            for step_run_output in step_run.step_run_outputs.all():
                channel_name = step_run_output.step_output.to_channel
                self._add_channel(step_run_output, channel_name)
        self._create_subchannels()
        self._add_input_data_objects_to_channels()
                
    def _add_channel(self, workflow_run_input_or_step_run_output, channel_name):
        channel = Channel.create({'channel_name': channel_name})
        self.channels.add(channel)
        workflow_run_input_or_step_run_output.add_channel(channel)

    def _get_channel_by_name(self, channel_name):
        return self.channels.get(channel_name=channel_name)

    def _create_subchannels(self):
        # One per workflow_run_ouput and step_run_input
        for workflow_run_output in self.workflow_run_outputs.all():
            channel_name = workflow_run_output.workflow_output.from_channel
            self._add_subchannel(workflow_run_output, channel_name)
        for step_run in self.step_runs.all():
            for step_run_input in step_run.step_run_inputs.all():
                channel_name = step_run_input.step_input.from_channel
                self._add_subchannel(step_run_input, channel_name)

    def _add_subchannel(workflow_run_output_or_step_run_input, channel_name):
        channel = self._get_channel_by_name(channel_name)
        subchannel = Subchannel.create()
        channel.add_subchannel(subchannel)
        workflow_run_output_or_step_run_input.add_subchannel(subchannel)
    
    def _add_input_data_objects_to_channels(self):
        for workflow_run_input in self.workflow_run_inputs.all():
            channel_name = workflow_run_input.workflow_input.channel_name
            channel = self._get_channel_by_name(channel_name)
            data_object = workflow_run_input.workflow_input.get_data_object(self)
            channel.add_data_object(data_object)

    def get_workflow_run_input_by_name(self, input_name):
        return self.workflow_run_inputs.get(input_name=input_name)
        
    
class WorkflowRunInput(AnalysisAppInstanceModel):
    """WorkflowRunInput serves as a binding between a DataObject and a Workflow input
    in a WorkflowRun
    """

    workflow_input = fields.ForeignKey('WorkflowInput')
    data_object = fields.ForeignKey('DataObject', null=True)
    channel = fields.ForeignKey('Channel', null=True)

    def add_channel(self, channel):
        self.update({'channel': channel.to_struct()})

class WorkflowRunOutput(AnalysisAppInstanceModel):

    workflow_output = fields.ForeignKey('WorkflowOutput')
    data_object = fields.ForeignKey('DataObject', null=True)
    subchannel = fields.ForeignKey('Subchannel', null=True)

    def add_subchannel(self, subchannel):
        self.update({'subchannel': subchannel.to_struct()})

class Channel(AnalysisAppInstanceModel):
    """Channel acts as a queue for data objects being being passed into or out of steps.
    """

    channel_name = fields.CharField(max_length=255)
    subchannels = fields.OneToManyField('Subchannel')
    # is_open==True indicates that more objects may arrive later
    is_open = fields.BooleanField(default=True)

    def add_data_object(self, data_object):
        for subchannel in self.subchannels.all():
            subchannel.add_data_object(data_object)
    
    def create_subchannel(self, workflow_run_output_or_step_run_input):
        subchannel = Subchannel.create()
        self.subchannels.add(subchannel)
        workflow_run_output_or_step_run_input.add_subchannel(subchannel)


class Subchannel(AnalysisAppInstanceModel):
    """Every channel can have only one source but 0 or many destinations, representing
    the possibility that a file produce by one step can be used by 0 or many other 
    steps. Each of these destinations has its own queue, implemented as a Subchannel.
    """

    data_objects = fields.OneToManyField('DataObject')

    def add_data_object(self, data_object):
        self.data_objects.add(data_object)

    def is_open(self):
        return self.channel.is_open


class StepRun(AnalysisAppInstanceModel):

    step = fields.ForeignKey('Step')
    status = fields.CharField(
        max_length=255,
        default='waiting',
        choices=(
            ('waiting', 'Waiting'),
            ('running', 'Running'),
            ('error', 'Error'),
            ('canceled', 'Canceled'),
            ('complete', 'Complete')
        )
    )
    status_message = fields.CharField(
        max_length=1000,
        default='Waiting...no details available yet.'
    )
    step_run_inputs = fields.OneToManyField('StepRunInput')
    step_run_outputs = fields.OneToManyField('StepRunOutput')
    
    def get_input_channels(self):
        pass
    
    def update_and_run(self):
        import pdb; pdb.set_trace()
        pass


class StepRunInput(AnalysisAppInstanceModel):
    step_input = fields.ForeignKey('StepInput')
    subchannel = fields.ForeignKey('Subchannel')

    def add_subchannel(self, subchannel):
        self.update({'subchannel': subchannel.to_struct()})

class StepRunOutput(AnalysisAppInstanceModel):
    step_output = fields.ForeignKey('StepOutput')

    def add_channel(self, channel):
        self.update({'channel': channel.to_struct()})
