from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import DataObject
from universalmodels import fields


"""
This module defines Workflow and other classes related to
receiving a request for analysis from a user.
"""


class WorkflowRun(AnalysisAppInstanceModel):
    """WorkflowRun represents a request to execute a Workflow on a particular
    set of inputs
    """

    NAME_FIELD = 'workflow__workflow_name'
    
    workflow = fields.ForeignKey('Workflow')
    workflow_run_inputs = fields.OneToManyField('WorkflowRunInput')
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
        workflow_run._create_step_runs()
        workflow_run._create_channels()
        workflow_run._create_subchannels()
        workflow_run._add_inputs_to_channels()
        # TODO Assign workflow status (probably w/ default field)
        return workflow_run

    def _create_step_runs(self):
        for step in self.workflow.steps.all():
            self._add_step_run(step)

    def _add_step_run(self, step):
        self.step_runs.add(
            StepRun.create({
                'step': step.to_struct()
            })
        )
    
    def _create_channels(self):
        # One per workflow_input and one per step_output
        for workflow_input in self.workflow.workflow_inputs.all():
            channel_name = workflow_input.get_channel_name()
            self._add_channel(channel_name)
        for step in self.workflow.steps.all():
            for step_output in step.step_outputs.all():
                self._add_channel(step_output.to_channel)
                
    def _add_channel(self, channel_name):
        self.channels.add(
            Channel.create(
                {'channel_name': channel_name}
            )
        )

    def _get_channel_by_name(self, channel_name):
        return self.channels.get(channel_name=channel_name)

    def _get_data_object(self, workflow_input):
        return workflow_input.get_data_object(self)

    def _create_subchannels(self):
        # One per workflow_ouput and step_input
        for workflow_output in self.workflow.workflow_outputs.all():
            channel_name = workflow_output.from_channel
            channel = self._get_channel_by_name(channel_name)
            channel.add_workflow_output_subchannel(workflow_output)
        for step in self.workflow.steps.all():
            for step_input in step.step_inputs.all():
                channel_name = step_input.from_channel
                channel = self._get_channel_by_name(channel_name)
                channel.add_step_input_subchannel(step, step_input)
        
    def _add_inputs_to_channels(self):
        for workflow_input in self.workflow.workflow_inputs.all():
            channel_name = workflow_input.get_channel_name()
            channel = self._get_channel_by_name(channel_name)
            data_object = self._get_data_object(workflow_input)
            channel.add_data_object(data_object)

    def get_workflow_run_input_by_name(self, input_name):
        return self.workflow_run_inputs.get(input_name=input_name)
        
    
class WorkflowRunInput(AnalysisAppInstanceModel):
    """WorkflowRunInput serves as a binding between a DataObject and a Workflow input
    in a WorkflowRun
    """

    input_name = fields.CharField(max_length=255)
    data_object = fields.ForeignKey('DataObject')


class Channel(AnalysisAppInstanceModel):
    """Channel acts as a queue for data objects being being passed into or out of steps.
    """

    channel_name = fields.CharField(max_length=255)
    subchannels = fields.OneToManyField('Subchannel')
    is_open = fields.BooleanField(default=True)

    def add_data_object(self, data_object):
        for subchannel in self.subchannels.all():
            subchannel.add_data_object(data_object)
    
    def add_workflow_output_subchannel(self, workflow_output):
        self.subchannels.add(
            Subchannel.create(
                {'workflow_output': workflow_output.to_struct()}
            )
        )

    def add_step_input_subchannel(self, step, step_input):
        self.subchannels.add(
            Subchannel.create(
                {
                    'step': step.to_struct(),
                    'step_input': step_input.to_struct()
                }
            )
        )
                                   
class Subchannel(AnalysisAppInstanceModel):
    """Every channel can have only one source but 0 or many destinations, representing
    the possibility that a file produce by one step can be used by 0 or many other 
    steps. Each of these destinations has its own queue, implemented as a Subchannel.
    """

    data_objects = fields.OneToManyField('DataObject')
    # The following are pointers to the data destination,
    # either a step, step_input pair, or a workflow_output.
    # Why are pointers to the destination here instead of the reverse?
    # Because Workflows and their children  are immutable, so
    # we can't add channels to those objects.
    step = fields.ForeignKey('Step', null=True)
    step_input = fields.ForeignKey('StepInput', null=True)
    workflow_output = fields.ForeignKey('WorkflowOutput', null=True)

    def add_data_object(self, data_object):
        self.data_objects.add(data_object)

class Workflow(AnalysisAppImmutableModel):
    """Each Workflow may contain many processing steps, with results from one
    step optionally feeding into another step as input.
    Workflows are ImmutableModels in order to prevent clutter. If the same workflow
    is uploaded multiple times, duplicate objects will not be created.
    """

    NAME_FIELD = 'workflow_name'

    workflow_name = fields.CharField(max_length=255)
    steps = fields.ManyToManyField('Step')
    workflow_inputs = fields.ManyToManyField('AbstractWorkflowInput')
    workflow_outputs = fields.ManyToManyField('WorkflowOutput')

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

    def update_and_run(self):
        pass

class Step(AnalysisAppImmutableModel):
    """Steps are smaller units of processing within a Workflow. A Step can give rise to a single process,
    or it may iterate over an array to produce many parallel processing tasks.
    """

    step_name = fields.CharField(max_length=255)
    command = fields.CharField(max_length=255)
    interpreter = fields.CharField(max_length=255)
    environment = fields.ForeignKey('RequestedEnvironment')
    resources = fields.ForeignKey('RequestedResourceSet')

    step_inputs = fields.ManyToManyField('StepInput')
    step_outputs = fields.ManyToManyField('StepOutput')


class RequestedEnvironment(AnalysisAppImmutableModel):

    pass


class RequestedDockerImage(RequestedEnvironment):

    docker_image = fields.CharField(max_length=255)


class RequestedResourceSet(AnalysisAppImmutableModel):

    memory = fields.CharField(max_length=255)
    disk_space = fields.CharField(max_length=255)
    cores = fields.IntegerField()


class AbstractWorkflowInput(AnalysisAppImmutableModel):

    def get_data_object(self, workflow_run):
        return self.downcast().get_data_object(workflow_run)

    def get_channel_name(self):
        return self.downcast().to_channel

class WorkflowInput(AbstractWorkflowInput):

    data_object = fields.ForeignKey(DataObject)
    to_channel = fields.CharField(max_length=255)

    def get_data_object(self, workflow_run):
        return self.data_object

class WorkflowInputPlaceholder(AbstractWorkflowInput):

    input_name = fields.CharField(max_length=255)
    to_channel = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            ('file_array', 'File Array'),
            ('boolean', 'Boolean'),
            ('boolean_array', 'Boolean Array'),
            ('string', 'String'),
            ('string_array', 'String Array'),
            ('integer', 'Integer'),
            ('integer_array', 'Integer Array'),
            ('float', 'Float'),
            ('float_array', 'Float Array'),
            ('json', 'JSON'),
            ('json_array', 'JSON Array')
        )
    )
    prompt = fields.CharField(max_length=255)

    def get_data_object(self, workflow_run):
        return workflow_run.get_workflow_run_input_by_name(self.input_name).data_object

class WorkflowOutput(AnalysisAppImmutableModel):

    from_channel = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)


class StepInput(AnalysisAppImmutableModel):

    from_channel = fields.CharField(max_length=255)
    to_path = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)


class StepOutput(AnalysisAppImmutableModel):

    from_path = fields.CharField(max_length=255)
    to_channel = fields.CharField(max_length=255)
    rename = fields.CharField(max_length=255)
