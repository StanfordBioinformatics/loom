from rest_framework import serializers

from .base import CreateWithParentModelSerializer, RecursiveField, \
    ProxyWriteSerializer, strip_empty_values, ExpandableSerializerMixin
from .input_output_nodes import InputOutputNodeSerializer
from api import async
from api.models.templates import Template, TemplateInput
from api.models.input_output_nodes import InputOutputNode


DEFAULT_INPUT_GROUP = 0
DEFAULT_INPUT_MODE = 'no_gather'
DEFAULT_OUTPUT_MODE = 'no_scatter'
DEFAULT_INTERPRETER = '/bin/bash -euo pipefail'

def _set_input_defaults(input):
    input.setdefault('group', DEFAULT_INPUT_GROUP)
    input.setdefault('mode', DEFAULT_INPUT_MODE)

def _set_output_defaults(output):
    output.setdefault('mode', DEFAULT_OUTPUT_MODE)

def _set_template_defaults(data, is_leaf):
    # Apply defaults for certain settings if missing
    if data.get('inputs'):
        for input in data.get('inputs'):
            _set_input_defaults(input)
    if data.get('outputs'):
        for output in data.get('outputs'):
            _set_output_defaults(output)
    data['is_leaf'] = is_leaf
    if is_leaf:
        # Set defaults for leaf node
        data.setdefault('interpreter', DEFAULT_INTERPRETER)
        
def _convert_template_id_to_dict(data):
    # If data is a string instead of a dict value,
    # set that as _template_id
    if not isinstance(data, dict):
        return {'_template_id': data}
    else:
        return data


class TemplateInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = TemplateInput
        fields = ('type', 'channel', 'data', 'hint', 'mode', 'group')

    hint = serializers.CharField(required=False)
    mode = serializers.CharField(required=False)
    group = serializers.IntegerField(required=False)
    data = serializers.JSONField(required=False) # Override to make non-required

    def create(self, validated_data):
        _set_input_defaults(validated_data)
        return super(TemplateInputSerializer, self).create(validated_data)


class TemplateURLSerializer(ProxyWriteSerializer):

    class Meta:
        model = Template
        fields = ('uuid',
                  'url',
                  'name',
                  'datetime_created',
                  'datetime_finished',
                  'status')

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='template-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    datetime_finished = serializers.DateTimeField(read_only=True, format='iso-8601')
    status = serializers.CharField(read_only=True)

    def to_internal_value(self, data):
        """Because we allow template ID string values, where
        serializers normally expect a dict
        """
        return _convert_template_id_to_dict(data)

    def get_target_serializer(self):
        return TemplateSerializer
        

class TemplateSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Template
        fields = ('uuid',
                  'url',
                  'name',
                  'datetime_created',
                  'command',
                  'comments',
                  'import_comments',
                  'imported_from_url',
                  'interpreter',
                  'environment',
                  'resources',
                  'postprocessing_status',
                  'inputs',
                  'outputs',
                  'steps',)

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
            view_name='template-detail',
            lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    command = serializers.CharField(required=False)
    comments = serializers.CharField(required=False)
    import_comments = serializers.CharField(required=False)
    imported_from_url = serializers.CharField(required=False)
    interpreter = serializers.CharField(required=False)
    environment = serializers.JSONField(required=False)
    resources = serializers.JSONField(required=False)
    postprocessing_status = serializers.CharField(required=False)
    inputs = TemplateInputSerializer(many=True, required=False)
    outputs  = serializers.JSONField(required=False)
    steps = TemplateURLSerializer(many=True, required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(TemplateSerializer, self).to_representation(instance))

    def to_internal_value(self, data):
        return _convert_template_id_to_dict(data)

    def create(self, validated_data):
        # If template_id is present, just look it up
        template_id = validated_data.get('_template_id')
        if template_id:
            return self._lookup_by_id(template_id)

        # Save inputs and steps for postprocessing
        validated_data['raw_data'] = self.initial_data
        validated_data.pop('inputs', None)
        steps = validated_data.pop('steps', None)
        is_leaf = not steps
        _set_template_defaults(validated_data, is_leaf)
        validated_data['imported'] = bool(validated_data.get('imported_from_url'))
        template = super(TemplateSerializer, self).create(validated_data)

        async.postprocess_template(template.uuid)

        return template

    def _lookup_by_id(self, template_id):
        matches = Template.filter_by_name_or_id(template_id)
        if matches.count() < 1:
            raise serializers.ValidationError(
                'No template found that matches value "%s"' % template_id)
        elif matches.count() > 1:
            match_id_list = ['%s@%s' % (match.name, match.uuid)
                             for match in matches]
            match_id_string = ('", "'.join(match_id_list))
            raise serializers.ValidationError(
                'Multiple templates were found matching value "%s": "%s". '\
                'Use a more precise identifier to select just one template.' % (
                    template_id, match_id_string))
        return  matches.first()
    
    @classmethod
    def postprocess(cls, template_uuid):
        template = Template.objects.get(uuid=template_uuid)
        try:
            inputs = template.raw_data.get('inputs', [])
            steps = template.raw_data.get('steps', [])
            for input_data in inputs:
                s = TemplateInputSerializer(
                    data=input_data,
                    context={'parent_field': 'template',
                             'parent_instance': template
                    })
                s.is_valid(raise_exception=True)
                s.save()
            for step_data in steps:
                s = TemplateSerializer(data=step_data)
                s.is_valid(raise_exception=True)
                step = s.save()
                template.add_step(step)
            template.postprocessing_status='complete'
            template.save()
        except Exception as e:
            template.postprocessing_status='failed'
            template.save
            raise

        # The user may have already submitted a run request before this
        # template finished postprocessing. If runs exist, postprocess them now.
        template = Template.objects.get(uuid=template.uuid)
        for run in template.runs.all():
            async.postprocess_run(run.uuid)

class NestedTemplateSerializer(TemplateSerializer):

    steps = RecursiveField(many=True, required=False)


class ExpandableTemplateSerializer(ExpandableSerializerMixin, TemplateSerializer):

    DEFAULT_SERIALIZER = TemplateSerializer
    COLLAPSE_SERIALIZER = TemplateSerializer
    EXPAND_SERIALIZER = NestedTemplateSerializer
    SUMMARY_SERIALIZER = NestedTemplateSerializer
