from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer,\
    IdSerializer
from api.models.templates import *
from api.models.input_output_nodes import InputOutputNode
from api.models.signals import post_save_children
from api import tasks
from .data_trees import DataNodeSerializer, DataNodeIdSerializer
from .input_output_nodes import InputOutputNodeSerializer


class FixedWorkflowInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = FixedWorkflowInput
        fields = ('type', 'channel', 'data')


class FixedStepInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = FixedStepInput
        fields = ('type', 'channel', 'data', 'mode', 'group')


class TemplateSerializer(SuperclassModelSerializer):

    type = serializers.CharField(required=False)

    class Meta:
        model = Template
        fields = '__all__'

    def _get_subclass_serializer_class(self, type):
        if type=='workflow':
            return WorkflowSerializer
        elif type=='step':
            return StepSerializer
        elif type=='lookup':
            # No valid type. Serialize with the base class
            return TemplateLookupSerializer

    def _get_subclass_field(self, type):
        if type == 'step':
            return 'step'
        elif type == 'workflow':
            return 'workflow'
        else:
            return None

    def _get_type(self, data=None, instance=None):
        if instance:
            return instance.type
        else:
            assert data, 'must provide either data or instance'
            explicit_type = data.get('type')
            if explicit_type:
                return explicit_type

            command = self.initial_data.get('command')
            steps = self.initial_data.get('steps')
            if steps and not command:
                return 'workflow'
            elif command and not steps:
                return 'step'
            elif data.get('_template_id'):
                return 'lookup'
            else:
                raise Exception('Unable to determine template type')

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            return {'_template_id': data}
        else:
            return data


class TemplateIdSerializer(IdSerializer, TemplateSerializer):

    pass


class StepSerializer(serializers.ModelSerializer):

    uuid = serializers.UUIDField(required=False)
    type = serializers.CharField(required=False)
    environment = serializers.JSONField(required=False)
    resources = serializers.JSONField(required=False)
    inputs = serializers.JSONField(required=False)
    fixed_inputs = FixedStepInputSerializer(many=True, required=False)
    outputs = serializers.JSONField(required=False)
    template_import =  serializers.JSONField(required=False)

    class Meta:
        model = Step
        fields = ('id',
                  'uuid',
                  'type',
                  'name',
                  'command',
                  'interpreter',
                  'environment',
                  'resources',
                  'inputs',
                  'fixed_inputs',
                  'outputs',
                  'datetime_created',
                  'template_import',)

    def create(self, validated_data):
        # Saved fixed inputs for postprocessing
        validated_data['raw_data'] = self.initial_data
        validated_data.pop('fixed_inputs', None)

        # Type might not be explicitly declared
        validated_data['type'] = 'step'

        step = super(StepSerializer, self).create(validated_data)

        tasks.postprocess_step.delay(step.id)

        return step

    @classmethod
    def postprocess(cls, step_id):
        step = Step.objects.get(id=step_id)
        fixed_inputs = step.raw_data.get('fixed_inputs', [])
        for fixed_input_data in fixed_inputs:
            s = FixedStepInputSerializer(
                data=fixed_input_data,
                context={'parent_field': 'step',
                         'parent_instance': step,
                     })
            s.is_valid(raise_exception=True)
            s.save()


class TemplateLookupSerializer(serializers.Serializer):

    _template_id = serializers.CharField(required=True)

    def create(self, validated_data):
        # If template_id is present, just look it up
        template_id = validated_data.get('_template_id')
        matches = Template.filter_by_name_or_id(template_id)
        if matches.count() < 1:
            raise Exception(
                'No match found for id %s' % template_id)
        elif matches.count() > 1:
            raise Exception(
                'Multiple workflows match id %s' % template_id)
        return  matches.first()


class WorkflowSerializer(serializers.ModelSerializer):

    uuid = serializers.UUIDField(required=False)
    type = serializers.CharField(required=False)
    inputs = serializers.JSONField(required=False)
    fixed_inputs = FixedWorkflowInputSerializer(
        many=True,
        required=False,
        allow_null=True)
    outputs = serializers.JSONField(required=False)
    steps = TemplateIdSerializer(many=True)
    template_import = serializers.JSONField(required=False)

    class Meta:
        model = Workflow
        fields = ('id',
                  'uuid',
                  'type',
                  'name',
                  'steps',
                  'inputs',
                  'fixed_inputs',
                  'outputs',
                  'datetime_created',
                  'template_import')

    def validate(self, data):
        steps = self.initial_data.get('steps', [])
        for step in steps:
            serializer = TemplateSerializer(data=step)
            serializer.is_valid(raise_exception=True)
        return data

    def create(self, validated_data):

        import datetime        
        tic = datetime.datetime.now()
        def toc(tic):
            toc = datetime.datetime.now() - tic
            return toc.total_seconds()

        # Ignore fixed_inputs and steps until postprocessing
        validated_data['raw_data'] = self.initial_data
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('steps', None)

        # Type may not be explicitly set
        validated_data['type'] = 'workflow'

        workflow = super(WorkflowSerializer, self).create(validated_data)

        x = tasks.postprocess_workflow.delay(workflow.id)
        import pdb; pdb.set_trace()
        return workflow

    @classmethod
    def postprocess(cls, workflow_id):
        workflow = Workflow.objects.get(id=workflow_id)
        fixed_inputs = workflow.raw_data.get('fixed_inputs', [])
        steps = workflow.raw_data.get('steps', [])

        for step_data in steps:
            s = TemplateSerializer(
                data=step_data)
            s.is_valid(raise_exception=True)
            step = s.save()
            workflow.add_step(step)

        for fixed_input_data in fixed_inputs:
            s = FixedWorkflowInputSerializer(
                data=fixed_input_data,
                context={'parent_field': 'workflow',
                         'parent_instance': workflow})
            s.is_valid(raise_exception=True)
            s.save()
