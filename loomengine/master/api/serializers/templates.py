from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer,\
    IdSerializer
from api.models.templates import *
from api.models.signals import post_save_children
from .input_output_nodes import InputOutputNodeDataFieldSerializer


class TemplateImportSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TemplateImport
        fields = ('note', 'source_url',)


class StepEnvironmentSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = StepEnvironment
        fields = ('docker_image',)


class StepResourceSetSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = StepResourceSet
        fields = ('memory', 'disk_size', 'cores',)


class WorkflowInputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = WorkflowInput
        fields = ('type', 'channel', 'hint',)


class StepInputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = StepInput
        fields = ('type', 'channel', 'hint', 'mode', 'group')


class FixedInputSerializer(InputOutputNodeDataFieldSerializer):

    def create(self, validated_data):
        data = validated_data.pop('data')

        if self.context.get('parent_field') \
           and self.context.get('parent_instance'):
            validated_data.update({
                self.context.get('parent_field'):
                self.context.get('parent_instance')})
        io_node =  self.Meta.model.objects.create(**validated_data)

        if data is not None:
            type = validated_data.get('type')
            if not type:
                raise Exception('data type is required')

            io_node.data_root = self._create_data_tree_from_data_objects(
                data, type)
            io_node.save()

        return io_node

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict.

            return super(self.__class__, self).to_representation(
                self.initial_data)
        else:
            assert isinstance(instance, InputOutputNode)
            # Execute "to_representation" on the correct subclass serializer
            #return {'data': self._data_tree_to_data_struct(instance.data_root)}
            return {}


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
                context = {'parent_field': 'output',
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


class TemplateSerializer(SuperclassModelSerializer):

    type = serializers.CharField(required=False)

    class Meta:
        model = Template
        fields = '__all__'

    def _get_subclass_serializer_class(self, type):
        if type=='workflow':
            return WorkflowSerializer
        elif type == 'step':
            return StepSerializer
        else:
            # No valid type. Serialize with the base class
            return TemplateSerializer

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
            else:
                raise Exception('Unable to idenify workflow type.')


class TemplateIdSerializer(IdSerializer, TemplateSerializer):

    pass


class StepSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    type = serializers.CharField(required=False)
    environment = StepEnvironmentSerializer()
    resources = StepResourceSetSerializer()
    inputs = StepInputSerializer(many=True, required=False)
    fixed_inputs = FixedStepInputSerializer(many=True, required=False)
    outputs = StepOutputSerializer(many=True)
    template_import = TemplateImportSerializer(allow_null=True, required=False)

    class Meta:
        model = Step
        fields = ('id',
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
        # Can't create inputs, outputs, environment, or resources until
        # step exists.
        inputs = self.initial_data.get('inputs', [])
        fixed_inputs = self.initial_data.get('fixed_inputs', [])
        outputs = self.initial_data.get('outputs', [])
        resources = self.initial_data.get('resources', None)
        environment = self.initial_data.get('environment', None)
        template_import = self.initial_data.get('workflow_import', None)
        validated_data['type'] = 'step'
        validated_data.pop('inputs', None)
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('outputs', None)
        validated_data.pop('resources', None)
        validated_data.pop('environment', None)
        validated_data.pop('template_import', None)

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
            s = StepResourceSetSerializer(
                data=resources,
                context={'parent_field': 'step',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

        if environment is not None:
            s = StepEnvironmentSerializer(
                data=environment,
                context={'parent_field': 'step',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

        if template_import is not None:
            s = TemplateImportSerializer(
                data=template_import,
                context={'parent_field': 'workflow',
                         'parent_instance': step})
            s.is_valid(raise_exception=True)
            s.save()

        return step


class WorkflowSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    type = serializers.CharField(required=False)
    inputs = WorkflowInputSerializer(
        many=True,
        required=False,
        allow_null=True)
    fixed_inputs = FixedWorkflowInputSerializer(
        many=True,
        required=False,
        allow_null=True)
    outputs = WorkflowOutputSerializer(many=True)
    steps = TemplateIdSerializer(many=True)
    template_import = TemplateImportSerializer(allow_null=True, required=False)

    class Meta:
        model = Workflow
        fields = ('id',
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
            serializer = TemplateSerializer(
                data=step,
                context=self.context)
            serializer.is_valid(raise_exception=True)
        return data

    def create(self, validated_data):
        # Can't create inputs or outputs until workflow exists
        inputs = self.initial_data.get('inputs', [])
        fixed_inputs = self.initial_data.get('fixed_inputs', [])
        outputs = self.initial_data.get('outputs', [])
        steps = self.initial_data.get('steps', [])
        template_import = self.initial_data.get('template_import', None)
        validated_data['type'] = 'workflow'
        validated_data.pop('inputs', None)
        validated_data.pop('fixed_inputs', None)
        validated_data.pop('outputs', None)
        validated_data.pop('steps', None)
        validated_data.pop('template_import', None)

        workflow = super(WorkflowSerializer, self).create(validated_data)

        new_steps = []
        for step_data in steps:
            s = TemplateSerializer(
                data=step_data,
                context=self.context)
            s.is_valid(raise_exception=True)
            new_steps.append(s.save())
        workflow.add_steps(new_steps)

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

        if template_import is not None:
            s = TemplateImportSerializer(
                data=template_import,
                context={'parent_field': 'workflow',
                         'parent_instance': workflow})
            s.is_valid(raise_exception=True)
            s.save()

        return workflow


"""

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
"""
