from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer
from api.models.workflows import *
from api.models.signals import post_save_children

class WorkflowImportSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = WorkflowImport
        fields = ('note', 'source_url',)


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
        fields = ('memory', 'disk_size', 'cores',)


class WorkflowInputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = WorkflowInput
        fields = ('type', 'channel', 'hint',)


class StepInputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = StepInput
        fields = ('type', 'channel', 'hint', 'mode', 'group')


class FixedInputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField() # converted from DataObject

    def create(self, validated_data):
        # Convert 'data' into its corresponding data object
        data = validated_data.pop('data')
        validated_data['data_object'] = DataObject.get_by_value(
            data,
            validated_data['type'])
        return super(FixedInputSerializer, self).create(validated_data)


class FixedWorkflowInputSerializer(FixedInputSerializer):

    class Meta:
        model = FixedWorkflowInput
        fields = ('type', 'channel', 'data')


class FixedStepInputSerializer(FixedInputSerializer):

    class Meta:
        model = FixedStepInput
        fields = ('type', 'channel', 'data', 'mode', 'group')


class WorkflowOutputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = WorkflowOutput
        fields = ('type', 'channel',)


class StepOutputSourceSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = StepOutputSource
        fields = ('filename', 'stream',)


#class StepOutputParserSerializer(CreateWithParentModelSerializer):
#
#    delimiter = serializers.CharField(required=False, allow_blank=True)
#
#    class Meta:
#        model = StepOutputParser
#        fields = ('delimiter',)


class StepOutputSerializer(CreateWithParentModelSerializer):

    source = StepOutputSourceSerializer()
    # parser = StepOutputParserSerializer(required=False)
    
    class Meta:
        model = StepOutput
        fields = ('type', 'channel', 'source', 'mode')

    def create(self, validated_data):
        source_data =self.initial_data.get('source', None)
        # parser_data =self.initial_data.get('parser', None)
        validated_data.pop('source', None)
        # validated_data.pop('parser', None)

        step_output = super(StepOutputSerializer, self).create(validated_data)

        if source_data:
            s = StepOutputSourceSerializer(
                data=source_data,
                context = {'parent_field': 'step_output',
                           'parent_instance': step_output})
            s.is_valid(raise_exception=True)
            s.save()

        #if parser_data:
        #    s = StepOutputParserSerializer(
        #        data=parser_data,
        #        context = {'parent_field': 'step_output',
        #                   'parent_instance': step_output})
        #    s.is_valid(raise_exception=True)
        #    s.save()

        post_save_children.send(sender=self.Meta.model, instance=step_output)
        return step_output


class AbstractWorkflowSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'workflow': 'api.serializers.workflows.WorkflowSerializer',
        'step': 'api.serializers.workflows.StepSerializer',
    }

    class Meta:
        model = AbstractWorkflow
        fields = '__all__'

class WorkflowSerializer(CreateWithParentModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
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
    workflow_import = WorkflowImportSerializer(allow_null=True, required=False)
    
    class Meta:
        model = Workflow
        fields = ('id',
                  'name',
                  'steps',
                  'inputs',
                  'fixed_inputs',
                  'outputs',
                  'datetime_created',
                  'workflow_import')

    def create(self, validated_data):
        # Can't create inputs or outputs until workflow exists
        inputs = self.initial_data.get('inputs', [])
        fixed_inputs = self.initial_data.get('fixed_inputs', [])
        outputs = self.initial_data.get('outputs', [])
        steps = self.initial_data.get('steps', [])
        workflow_import = self.initial_data.get('workflow_import', None)
        
        validated_data.pop('inputs', None)
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('outputs', None)
        validated_data.pop('steps', None)
        validated_data.pop('workflow_import', None)
        
        workflow = super(WorkflowSerializer, self).create(validated_data)

        for step_data in steps:
            s = AbstractWorkflowSerializer(
                data=step_data,
                context = {'parent_field': 'parent_workflow',
                           'parent_instance': workflow})
            s.is_valid(raise_exception=True)
            s.save()

        for input_data in inputs:
            s = WorkflowInputSerializer(
                data=input_data,
                context={'parent_field': 'workflow',
                         'parent_instance': workflow})
            s.is_valid(raise_exception=True)
            s.save()

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

        if workflow_import is not None:
            s = WorkflowImportSerializer(
                data=workflow_import,
                context={'parent_field': 'workflow',
                         'parent_instance': workflow})
            s.is_valid(raise_exception=True)
            s.save()

        post_save_children.send(sender=self.Meta.model, instance=workflow)
        return workflow


class StepSerializer(CreateWithParentModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    environment = RequestedEnvironmentSerializer()
    resources = RequestedResourceSetSerializer()
    inputs = StepInputSerializer(many=True, required=False)
    fixed_inputs = FixedStepInputSerializer(many=True, required=False)
    outputs = StepOutputSerializer(many=True)
    workflow_import = WorkflowImportSerializer(allow_null=True, required=False)

    class Meta:
        model = Step
        fields = ('id',
                  'name',
                  'command',
                  'interpreter',
                  'environment',
                  'resources',
                  'inputs',
                  'fixed_inputs',
                  'outputs',
                  'datetime_created',
                  'workflow_import',)

    def create(self, validated_data):
        # Can't create inputs, outputs, environment, or resources until
        # step exists.
        inputs = self.initial_data.get('inputs', [])
        fixed_inputs = self.initial_data.get('fixed_inputs', [])
        outputs = self.initial_data.get('outputs', [])
        resources = self.initial_data.get('resources', None)
        environment = self.initial_data.get('environment', None)
        workflow_import = self.initial_data.get('workflow_import', None)
        validated_data.pop('inputs', None)
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('outputs', None)
        validated_data.pop('resources', None)
        validated_data.pop('environment', None)
        validated_data.pop('workflow_import', None)
        
        step = super(StepSerializer, self).create(validated_data)

        for input_data in inputs:
            s = StepInputSerializer(
                data=input_data,
                context={'parent_field': 'step',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

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
            s = RequestedEnvironmentSerializer(
                data=environment,
                context={'parent_field': 'step',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

        if workflow_import is not None:
            s = WorkflowImportSerializer(
                data=workflow_import,
                context={'parent_field': 'workflow',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

        return step

class AbstractWorkflowIdSerializer(serializers.Serializer):

    def to_representation(self, obj):
        return obj.get_name_and_id()

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            return {'template_id': data}
        else:
            return data

    def create(self, validated_data):
        # We don't create a new object, but look up one that
        # matches the given ID if it exists.
        matches = AbstractWorkflow.filter_by_name_or_id(
            validated_data['template_id'])
        if matches.count() < 1:
            raise Exception(
                'No match found for id %s' % validated_data['template_id'])
        elif matches.count() > 1:
            raise Exception(
                'Multiple workflows match id %s' % validated_data[
                    'template_id'])
        return  matches.first()
