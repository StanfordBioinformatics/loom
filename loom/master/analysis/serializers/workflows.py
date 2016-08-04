from rest_framework import serializers

from .base import CreateWithParentModelSerializer, NoUpdateModelSerializer, \
    SuperclassModelSerializer
from analysis.models.workflows import *
from analysis.serializers.data_objects import DataObjectValueSerializer


class RequestedDockerEnvironmentSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RequestedDockerEnvironment
        fields = ('docker_image',)


class RequestedEnvironmentSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'requesteddockerenvironment': RequestedDockerEnvironmentSerializer,
        
    }

    class Meta:
        model = RequestedEnvironment
        fields = ()


class RequestedResourceSetSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RequestedResourceSet
        fields = ('memory', 'disk_space', 'cores',)


class WorkflowInputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = WorkflowInput
        fields = ('type', 'channel', 'hint',)


class StepInputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = StepInput
        fields = ('type', 'channel', 'hint',)


class FixedInputSerializer(CreateWithParentModelSerializer):

    def create(self, validated_data):
        # Convert 'value' into its corresponding data object
        s1 = DataObjectValueSerializer(
            data=self.initial_data['value'],
            context={'type': validated_data['type']})
        s1.is_valid()
        validated_data['data_object'] = s1.save()

        return super(FixedInputSerializer, self).create(validated_data)


class FixedWorkflowInputSerializer(FixedInputSerializer):

    class Meta:
        model = FixedWorkflowInput
        fields = ('type', 'channel')


class FixedStepInputSerializer(FixedInputSerializer):

    class Meta:
        model = FixedStepInput
        fields = ('type', 'channel')


class WorkflowOutputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = WorkflowOutput
        fields = ('type', 'channel',)


class StepOutputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = StepOutput
        fields = ('type', 'channel', 'filename')


class AbstractWorkflowSerializer(SuperclassModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    subclass_serializers = {
        'workflow': 'analysis.serializers.workflows.WorkflowSerializer',
        'step': 'analysis.serializers.workflows.StepSerializer',
    }

    class Meta:
        model = AbstractWorkflow


class WorkflowSerializer(CreateWithParentModelSerializer):

    inputs = WorkflowInputSerializer(
        many=True,
        required=False,
        allow_null=True)
    fixed_inputs = FixedWorkflowInputSerializer(
        many=True,
        required=False,
        allow_null=True)
    outputs = WorkflowOutputSerializer(many=True)
    steps = AbstractWorkflowSerializer(many=True)
    
    class Meta:
        model = Workflow
        fields = ('id', 'name', 'steps', 'inputs', 'fixed_inputs', 'outputs',)

    def create(self, validated_data):
        # Can't create inputs or outputs until workflow exists
        inputs = self.initial_data.get('inputs', None)
        fixed_inputs = self.initial_data.get('fixed_inputs', None)
        outputs = self.initial_data.get('outputs', None)
        steps = self.initial_data.get('steps', None)
        
        validated_data.pop('inputs', None)
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('outputs', None)
        validated_data.pop('steps', None)

        workflow = Workflow.objects.create(**validated_data)

        for step_data in steps:
            s = AbstractWorkflowSerializer(
                data=step_data,
                context = {'parent_field': 'parent_workflow',
                           'parent_instance': workflow})
            s.is_valid(raise_exception=True)
            s.save()

        if inputs is not None:
            for input_data in inputs:
                s = WorkflowInputSerializer(
                    data=input_data,
                    context={'parent_field': 'workflow',
                             'parent_instance': workflow})
                s.is_valid(raise_exception=True)
                s.save()

        if fixed_inputs is not None:
            for fixed_input_data in fixed_inputs:
                s = FixedWorkflowInputSerializer(
                    data=fixed_input_data,
                    context={'parent_field': 'workflow',
                             'parent_instance': workflow})
                s.is_valid(raise_exception=True)

                s.save()

        for output_data in outputs:
            s = WorkflowOutputSerializer(
                data=output_data,
                context={'parent_field': 'workflow',
                         'parent_instance': workflow})
            s.is_valid(raise_exception=True)
            s.save()
                
        return workflow


class StepSerializer(CreateWithParentModelSerializer):

    environment = RequestedEnvironmentSerializer()
    resources = RequestedResourceSetSerializer()
    inputs = StepInputSerializer(many=True, required=False)
    fixed_inputs = FixedStepInputSerializer(many=True, required=False)
    outputs = StepOutputSerializer(many=True)

    class Meta:
        model = Step
        fields = ('id',
                  'name',
                  'command',
                  'environment',
                  'resources',
                  'inputs',
                  'fixed_inputs',
                  'outputs',)

    def create(self, validated_data):
        # Can't create inputs, outputs, environment, or resources until
        # step exists.
        inputs = self.initial_data.get('inputs', None)
        fixed_inputs = self.initial_data.get('fixed_inputs', None)
        outputs = self.initial_data.get('outputs', None)
        resources = self.initial_data.get('resources', None)
        environment = self.initial_data.get('environment', None)
        validated_data.pop('inputs', None)
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('outputs', None)
        validated_data.pop('resources', None)
        validated_data.pop('environment', None)
        
        step = Step.objects.create(**validated_data)

        if inputs is not None:
            for input_data in inputs:
                s = StepInputSerializer(
                    data=input_data,
                    context={'parent_field': 'step',
                             'parent_instance': step})
                s.is_valid(raise_exception=True)
                s.save()

        if fixed_inputs is not None:
            for fixed_input_data in fixed_inputs:
                s = FixedStepInputSerializer(
                    data=fixed_input_data,
                    context={'parent_field': 'step',
                             'parent_instance': step})
                s.is_valid(raise_exception=True)

                s.save()

        for output_data in outputs:
            s = StepOutputSerializer(
                data=output_data,
                context={'parent_field': 'step',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()
                
        if resources is not None:
            s = RequestedResourceSetSerializer(
                data=resources,
                context={'parent_field': 'step',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

        if environment is not None:
            RequestedEnvironmentSerializer(
                data=environment,
                context={'parent_field': 'step',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

        return step
