from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, \
    NameAndUuidSerializer
from api.models.runs import Run, StepRun, \
    StepRunInput, StepRunOutput, WorkflowRunInput, \
    WorkflowRunOutput, WorkflowRun
from api.serializers.templates import TemplateNameAndUuidSerializer
from api.serializers.tasks import TaskUuidSerializer, \
    TaskAttemptErrorSerializer
from api.serializers.input_output_nodes import InputOutputNodeSerializer
from api.serializers.run_requests import RunRequestSerializer, \
    RunRequestUuidSerializer
from api import tasks


class RunSerializer(SuperclassModelSerializer):

    class Meta:
        model = Run
        fields = '__all__'

    def _get_subclass_serializer_class(self, type):
        if type=='workflow':
            return WorkflowRunSerializer
        if type=='step':
            return StepRunSerializer
        else:
            # No valid type. Serializer with the base class
            return RunSerializer

    def _get_subclass_field(self, type):
        if type == 'step':
            return 'steprun'
        elif type == 'workflow':
            return 'workflowrun'
        else:
            return None

    def _get_type(self, data=None, instance=None):
        if instance:
            type = instance.type
        else:
            assert data, 'must provide either data or instance'
            type = data.get('type')
        if not type:
            return None
        return type

    @classmethod
    def create_from_template(cls, template, parent=None, no_delay=True):
        if template.type == 'step':
            run = StepRun.objects.create(template=template,
                                         name=template.name,
                                         type=template.type,
                                         command=template.step.command,
                                         interpreter=template.step.interpreter,
                                         parent=parent).run_ptr
            if no_delay:
                tasks._postprocess_step_run(run.id)
            else:
                tasks.postprocess_step_run(run.id)
        else:
            assert template.type == 'workflow', \
                'Invalid template type "%s"' % template.type
            run = WorkflowRun.objects.create(template=template,
                                             name=template.name,
                                             type=template.type,
                                             parent=parent).run_ptr
            if no_delay:
                tasks._postprocess_workflow_run(run.id)
            else:
                tasks.postprocess_workflow_run(run.id)

        return run


class RunNameAndUuidSerializer(NameAndUuidSerializer, RunSerializer):
    pass


class StepRunInputSerializer(InputOutputNodeSerializer):

    mode = serializers.CharField()
    group = serializers.IntegerField()

    class Meta:
        model = StepRunInput
        fields = ('type', 'channel', 'data', 'mode', 'group')


class StepRunOutputSerializer(InputOutputNodeSerializer):

    mode = serializers.CharField()

    class Meta:
        model = StepRunOutput
        fields = ('type', 'channel', 'data', 'mode')

def _get_destinations(run):
    return [dest for dest in run.inputs.all()]

def _get_source(run, channel):
    # Four possible sources for this step's inputs:
    # 1. inputs from parent
    # 2. outputs from siblings
    # 3. user-provided inputs in run_request
    # 4. fixed_inputs on template
    sources = []
    if run.parent:
        sources.extend(run.parent.inputs.filter(channel=channel))
        siblings = run.parent.workflowrun.steps.exclude(id=run.id)
        for sibling in siblings:
            sources.extend(sibling.outputs.filter(channel=channel))
    try:
        run_request = run.run_request
        sources.extend(run_request.inputs.filter(channel=channel))
    except ObjectDoesNotExist:
        pass
    sources.extend(run.template.fixed_inputs.filter(channel=channel))
    assert len(sources) == 1
    return sources[0]

def _connect_channels(run):
    # Channels must be connected in order from the outside in,
    # so this function connects the current run outward
    # but does not connect to its steps.
    for destination in _get_destinations(run):
        source = _get_source(run, destination.channel)
        # Make sure matching source and destination nodes are connected
        source.connect(destination)
    try:
        for step in run.workflowrun.steps.all():
            _connect_channels(step)
    except ObjectDoesNotExist:
        # run.workflowrun does not exist for a StepRun
        pass


class StepRunSerializer(CreateWithParentModelSerializer):
    
    uuid = serializers.UUIDField(format='hex', required=False)
    template = TemplateNameAndUuidSerializer()
    inputs = StepRunInputSerializer(many=True,
                                    required=False,
                                    allow_null=True)
    outputs = StepRunOutputSerializer(many=True)
    command = serializers.CharField()
    interpreter = serializers.CharField()
    type = serializers.CharField()
    tasks = TaskUuidSerializer(many=True)
    run_request = RunRequestUuidSerializer(required=False)
#    errors = TaskAttemptErrorSerializer(many=True, read_only=True)
    
    class Meta:
        model = StepRun
        fields = ('uuid', 'template', 'inputs', 'outputs',
                  'command', 'interpreter', 'tasks', 'run_request',
                  'saving_status', 'type')

    @classmethod
    def postprocess(cls, run_id):
        run = StepRun.objects.get(id=run_id)
        try:
            cls._initialize_inputs(run)
            cls._initialize_outputs(run)

            # connect_channels must be triggered on the topmost parent.
            # This will connect channels on children as well.
            if run.parent is None:
                _connect_channels(run)

            run.saving_status = 'ready'
            run.save()
        except Exception as e:
            run.saving_status = 'error'
            run.save()
            raise e

    @classmethod
    def _initialize_inputs(cls, run):
        all_channels = set()
        for input in run.template.inputs:
            assert input.get('channel') not in all_channels
            all_channels.add(input.get('channel'))

            StepRunInput.objects.create(
                step_run=run,
                channel=input.get('channel'),
                type=input.get('type'),
                group=input.get('group'),
                mode=input.get('mode'))

        for fixed_input in run.template.fixed_inputs.all():
            assert fixed_input.channel not in all_channels
            all_channels.add(fixed_input.channel)

            StepRunInput.objects.create(
                step_run=run,
                channel=fixed_input.channel,
                type=fixed_input.type,
                group=input.group,
                mode=input.mode)

    @classmethod
    def _initialize_outputs(cls, run):
        all_channels = set()
        for output in run.template.outputs:
            assert output.get('channel') not in all_channels
            all_channels.add(output.get('channel'))

            StepRunOutput.objects.create(
                step_run=run,
                type=output.get('type'),
                channel=output.get('channel'))


class WorkflowRunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = WorkflowRunInput
        fields = ('type', 'channel', 'data',)


class WorkflowRunOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = WorkflowRunOutput
        fields = ('type', 'channel', 'data',)


class WorkflowRunSerializer(CreateWithParentModelSerializer):

    uuid = serializers.UUIDField(format='hex', required=False)
    type = serializers.CharField(required=False)
    template = TemplateNameAndUuidSerializer()
    steps = RunNameAndUuidSerializer(many=True)
    inputs = WorkflowRunInputSerializer(many=True,
                                        required=False,
                                        allow_null=True)
    outputs = WorkflowRunOutputSerializer(many=True)
    run_request = RunRequestUuidSerializer(required=False)

    class Meta:
        model = WorkflowRun
        fields = ('uuid', 'template', 'steps', 'inputs', 'outputs',
                  'run_request', 'saving_status', 'type')

    @classmethod
    def postprocess(cls, run_id):
        run = WorkflowRun.objects.get(id=run_id)
        try:
            cls._initialize_inputs(run)
            cls._initialize_outputs(run)
            cls._initialize_steps(run)

            # connect_channels must be triggered on the topmost parent.
            # This will connect channels on children as well.
            if run.parent is None:
                _connect_channels(run)

            run.saving_status = 'ready'
            run.save()
        except Exception as e:
            run.saving_status = 'error'
            run.save()
            raise e

    @classmethod
    def _initialize_inputs(cls, run):
        all_channels = set()
        for input in run.template.inputs:
            assert input.get('channel') not in all_channels
            all_channels.add(input.get('channel'))

            WorkflowRunInput.objects.create(
                workflow_run=run,
                channel=input.get('channel'),
                type=input.get('type'))

        for fixed_input in run.template.fixed_inputs.all():
            assert fixed_input.channel not in all_channels
            all_channels.add(fixed_input.channel)

            WorkflowRunInput.objects.create(
                workflow_run=run,
                channel=fixed_input.channel,
                type=fixed_input.type)

    @classmethod
    def _initialize_outputs(cls, run):
        all_channels = set()
        for output in run.template.outputs:
            assert output.get('channel') not in all_channels
            all_channels.add(output.get('channel'))

            WorkflowRunOutput.objects.create(
                workflow_run=run,
                type=output.get('type'),
                channel=output.get('channel'))

    @classmethod
    def _initialize_steps(cls, run):
        for step in run.template.workflow.steps.all():
            RunSerializer.create_from_template(step, parent=run, no_delay=True)
