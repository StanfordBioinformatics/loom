from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, IdSerializer
from api.models.runs import Run, StepRun, \
    StepRunInput, FixedStepRunInput, StepRunOutput, WorkflowRunInput, \
    FixedWorkflowRunInput, WorkflowRunOutput, WorkflowRun
from api.serializers.templates import TemplateIdSerializer
from api.serializers.tasks import TaskIdSerializer, TaskAttemptErrorSerializer
from api.serializers.input_output_nodes import InputOutputNodeSerializer


class RunSerializer(SuperclassModelSerializer):

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
            raise Exception('Unable to identify run type')
        return type

    subclass_serializers = {
        'workflowrun': 'api.serializers.WorkflowRunSerializer',
        'steprun': 'api.serializers.StepRunSerializer'
    }

    class Meta:
        model = Run
        fields = '__all__'

class RunIdSerializer(IdSerializer, RunSerializer):
    pass


class StepRunInputSerializer(InputOutputNodeSerializer):

    mode = serializers.CharField()
    group = serializers.IntegerField()

    class Meta:
        model = StepRunInput
        fields = ('type', 'channel', 'data', 'mode', 'group')


class FixedStepRunInputSerializer(InputOutputNodeSerializer):

    mode = serializers.CharField()
    group = serializers.IntegerField()
        
    class Meta:
        model = FixedStepRunInput
        fields = ('type', 'channel', 'data', 'mode', 'group')

        
class StepRunOutputSerializer(InputOutputNodeSerializer):

    mode = serializers.CharField()

    class Meta:
        model = StepRunOutput
        fields = ('type', 'channel', 'data', 'mode')


class StepRunSerializer(CreateWithParentModelSerializer):
    
    uuid = serializers.UUIDField(format='hex', required=False)
    template = TemplateIdSerializer()
    inputs = StepRunInputSerializer(many=True,
                                    required=False,
                                    allow_null=True)
    fixed_inputs = FixedStepRunInputSerializer(many=True,
                                               required=False,
                                               allow_null=True)
    outputs = StepRunOutputSerializer(many=True)
    command = serializers.CharField()
    interpreter = serializers.CharField()
    name = serializers.CharField()
    tasks = TaskIdSerializer(many=True)
#    errors = TaskAttemptErrorSerializer(many=True, read_only=True)
    
    class Meta:
        model = StepRun
        fields = ('id', 'uuid', 'template', 'inputs', 'fixed_inputs', 
                  'outputs', 'command', 'interpreter', 'name', 'tasks')


class WorkflowRunInputSerializer(InputOutputNodeSerializer):
        
    class Meta:
        model = WorkflowRunInput
        fields = ('type', 'channel', 'data',)


class FixedWorkflowRunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = FixedWorkflowRunInput
        fields = ('type', 'channel', 'data',)


class WorkflowRunOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = WorkflowRunOutput
        fields = ('type', 'channel', 'data',)


class WorkflowRunSerializer(CreateWithParentModelSerializer):

    uuid = serializers.UUIDField(format='hex', required=False)
    template = TemplateIdSerializer()
    steps = RunIdSerializer(many=True)
    inputs = WorkflowRunInputSerializer(many=True,
                                        required=False,
                                        allow_null=True)
    fixed_inputs = FixedWorkflowRunInputSerializer(many=True,
                                                   required=False,
                                                   allow_null=True)
    outputs = WorkflowRunOutputSerializer(many=True)
    name = serializers.CharField()
    
    class Meta:
        model = WorkflowRun
        fields = ('id', 'uuid', 'template', 'steps', 'inputs', 'fixed_inputs',
                  'outputs', 'name')
