from rest_framework import serializers
from django.db import transaction

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer,\
    NameAndUuidSerializer
from api.models.templates import *
from api.models.input_output_nodes import InputOutputNode
from api.models.signals import post_save_children
from api import tasks
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


class TemplateNameAndUuidSerializer(NameAndUuidSerializer, TemplateSerializer):

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
    postprocessing_status = serializers.CharField(required=False)

    class Meta:
        model = Step
        fields = ('uuid',
                  'type',
                  'name',
                  'command',
                  'interpreter',
                  'interpreter_options',
                  'environment',
                  'resources',
                  'inputs',
                  'fixed_inputs',
                  'outputs',
                  'datetime_created',
                  'template_import',
                  'postprocessing_status',
        )

    def create(self, validated_data):
        # Save fixed inputs for postprocessing
        validated_data['raw_data'] = self.initial_data
        validated_data.pop('fixed_inputs', None)

        # Apply defaults for certain settings if missing
        inputs = validated_data.get('inputs')
        outputs = validated_data.get('outputs')
        if inputs:
            for input in inputs:
                self._set_input_defaults(input)
        if outputs:
            for output in outputs:
                self._set_output_defaults(output)

        # Type might not be explicitly declared
        validated_data['type'] = 'step'

        with transaction.atomic():
            step = super(StepSerializer, self).create(validated_data)

        tasks.postprocess_step(step.id)

        return step

    def _set_input_defaults(self, input):
        input.setdefault('group', DEFAULT_INPUT_GROUP)
        input.setdefault('mode', DEFAULT_INPUT_MODE)

    def _set_output_defaults(self, output):
        output.setdefault('group', DEFAULT_OUTPUT_MODE)

    @classmethod
    def postprocess(cls, step_id):
        step = Step.objects.get(id=step_id)
        try:
            fixed_inputs = step.raw_data.get('fixed_inputs', [])
            for fixed_input_data in fixed_inputs:
                s = FixedStepInputSerializer(
                    data=fixed_input_data,
                    context={'parent_field': 'step',
                             'parent_instance': step,
                    })
                s.is_valid(raise_exception=True)
                s.save()

            step.postprocessing_status='done'
            step.save()
        except Exception as e:
            step.postprocessing_status='error'
            step.save
            raise e

        # The user may have already submitted a run request before this
        # template finished postprocessing. If runs exist, postprocess them now.
        for step_run in step.runs.all():
            tasks.postprocess_step_run(step_run.id)


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
    steps = TemplateNameAndUuidSerializer(many=True)
    template_import = serializers.JSONField(required=False)
    postprocessing_status = serializers.CharField(required=False)

    class Meta:
        model = Workflow
        fields = ('uuid',
                  'type',
                  'name',
                  'steps',
                  'inputs',
                  'fixed_inputs',
                  'outputs',
                  'datetime_created',
                  'template_import',
                  'postprocessing_status',)

    def create(self, validated_data):

        # Ignore fixed_inputs and steps until postprocessing
        validated_data['raw_data'] = self.initial_data
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('steps', None)

        # Type may not be explicitly set
        validated_data['type'] = 'workflow'

        with transaction.atomic():
            workflow = super(WorkflowSerializer, self).create(validated_data)

        tasks.postprocess_workflow(workflow.id)

        return workflow

    @classmethod
    def postprocess(cls, workflow_id):

        workflow = Workflow.objects.get(id=workflow_id)
        try:
            fixed_inputs = workflow.raw_data.get('fixed_inputs', [])
            steps = workflow.raw_data.get('steps', [])

            for fixed_input_data in fixed_inputs:
                s = FixedWorkflowInputSerializer(
                    data=fixed_input_data,
                    context={'parent_field': 'workflow',
                             'parent_instance': workflow})
                s.is_valid(raise_exception=True)
                s.save()

            for step_data in steps:
                s = TemplateSerializer(data=step_data)
                s.is_valid(raise_exception=True)
                step = s.save()
                workflow.add_step(step)

            workflow.postprocessing_status = 'done'
            workflow.save()

            # There are only runs if the user submitted a run with this
            # template before we finished postprocessing the template. The run's
            # postprocessing is skipped if its template is not
            # postprocessing_status==done.

            for workflow_run in workflow.runs.all():
                tasks.postprocess_workflow_run(workflow_run.id)

        except Exception as e:
            workflow.postprocessing_status = 'error'
            workflow.save()
            raise e
