import copy
from rest_framework import serializers

from .base import CreateWithParentModelSerializer, RecursiveField, \
    ProxyWriteSerializer, strip_empty_values, ExpandableSerializerMixin
from .data_channels import DataChannelSerializer
from api import async
from api.models.templates import Template, TemplateInput
from api.models.data_channels import DataChannel


DEFAULT_INPUT_GROUP = 0
DEFAULT_INPUT_MODE = 'no_gather'
DEFAULT_OUTPUT_MODE = 'no_scatter'
DEFAULT_INTERPRETER = '/bin/bash -euo pipefail'

def _set_leaf_input_defaults(input):
    input.setdefault('group', DEFAULT_INPUT_GROUP)
    input.setdefault('mode', DEFAULT_INPUT_MODE)

def _set_leaf_template_defaults(data):
    # Apply defaults for certain settings if missing
    if data.get('outputs'):
        for output in data.get('outputs'):
            output.setdefault('mode', DEFAULT_OUTPUT_MODE)
    data.setdefault('interpreter', DEFAULT_INTERPRETER)
        
def _convert_template_id_to_dict(data):
    # If data is a string instead of a dict value,
    # set that as _template_id
    if isinstance(data, (str, unicode)):
        return {'_template_id': data}
    else:
        return data


class TemplateInputSerializer(DataChannelSerializer):

    class Meta:
        model = TemplateInput
        fields = ('type', 'channel', 'data', 'hint', 'mode', 'group')

    hint = serializers.CharField(required=False)
    mode = serializers.CharField(required=False)
    group = serializers.IntegerField(required=False)
    data = serializers.JSONField(required=False) # Override to make non-required

    def create(self, validated_data):
        if self.context.get('is_leaf'):
            _set_leaf_input_defaults(validated_data)
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
        return super(TemplateURLSerializer, self).to_internal_value(
            _convert_template_id_to_dict(data))

    def get_target_serializer(self):
        return TemplateSerializer


class TemplateSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Template
        fields = ('uuid',
                  'url',
                  '_template_id',
                  'name',
                  'datetime_created',
                  'command',
                  'comments',
                  'import_comments',
                  'imported_from_url',
                  'is_leaf',
                  'interpreter',
                  'environment',
                  'resources',
                  'postprocessing_status',
                  'inputs',
                  # Fixed inputs are deprecated
                  'fixed_inputs',
                  'outputs',
                  'steps',)

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
            view_name='template-detail',
            lookup_field='uuid')
    _template_id = serializers.CharField(write_only=True, required=False)
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    command = serializers.CharField(required=False)
    comments = serializers.CharField(required=False)
    import_comments = serializers.CharField(required=False)
    imported_from_url = serializers.CharField(required=False)
    is_leaf = serializers.BooleanField(required=False)
    interpreter = serializers.CharField(required=False)
    environment = serializers.JSONField(required=False)
    resources = serializers.JSONField(required=False)
    postprocessing_status = serializers.CharField(required=False)
    inputs = TemplateInputSerializer(many=True, required=False)
    # Fixed inputs are deprecated
    fixed_inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
    outputs  = serializers.JSONField(required=False)
    steps = TemplateURLSerializer(many=True, required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(TemplateSerializer, self).to_representation(instance))

    def to_internal_value(self, data):
        return super(TemplateSerializer, self).to_internal_value(
            _convert_template_id_to_dict(data))

    def create(self, validated_data):
        # If template_id is present, just look it up
        template_id = validated_data.get('_template_id')
        if template_id:
            return self._lookup_by_id(template_id)

        # Save inputs and steps for postprocessing
        validated_data['raw_data'] = self.initial_data
        validated_data.pop('inputs', None)
        validated_data.pop('fixed_inputs', None)

        steps = validated_data.pop('steps', None)
        if validated_data.get('is_leaf') is None:
            validated_data['is_leaf'] = not steps
        if validated_data['is_leaf']:
            _set_leaf_template_defaults(validated_data)
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
            inputs = copy.deepcopy(template.raw_data.get('inputs', []))

            # Fixed inputs are deprecated
            fixed_inputs = copy.deepcopy(template.raw_data.get('fixed_inputs', []))
            inputs.extend(fixed_inputs)

            steps = template.raw_data.get('steps', [])
            for input_data in inputs:
                s = TemplateInputSerializer(
                    data=input_data,
                    context={'parent_field': 'template',
                             'parent_instance': template,
                             'is_leaf': template.is_leaf
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
