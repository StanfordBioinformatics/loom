import copy
from django.db.models import Prefetch
from rest_framework import serializers

from . import CreateWithParentModelSerializer, RecursiveField, \
    ProxyWriteSerializer, strip_empty_values
from .data_channels import DataChannelSerializer
from api import async
from api.models.templates import Template, TemplateInput, TemplateMembership
from api.models.data_channels import DataChannel
from api.serializers import DataNodeSerializer


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
        fields = ('type', 'channel', 'as_channel', 'data', 'hint', 'mode', 'group')

    hint = serializers.CharField(required=False)
    mode = serializers.CharField(required=False)
    group = serializers.IntegerField(required=False)
    data = serializers.JSONField(required=False) # Override to make non-required
    as_channel = serializers.CharField(required=False)


_template_serializer_fields = (
    'uuid',
    'url',
    '_template_id',
    'name',
    'md5',
    'datetime_created',
    'command',
    'comments',
    'import_comments',
    'imported_from_url',
    'is_leaf',
    'interpreter',
    'environment',
    'resources',
    'inputs',
    # Fixed inputs are deprecated
    'fixed_inputs',
    'outputs',
    'steps',)


class URLTemplateSerializer(ProxyWriteSerializer):

    class Meta:
        model = Template
        fields = _template_serializer_fields

    # readable
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='template-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    md5 = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(
        format='iso-8601', required=False)
    is_leaf = serializers.BooleanField(required=False)

    # write-only
    _template_id = serializers.CharField(write_only=True, required=False)
    command = serializers.CharField(required=False, write_only=True)
    comments = serializers.CharField(required=False, write_only=True)
    import_comments = serializers.CharField(required=False, write_only=True)
    imported_from_url = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
    # Fixed inputs are deprecated
    fixed_inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
    outputs  = serializers.JSONField(required=False, write_only=True)
    steps = RecursiveField(many=True, required=False, write_only=True)

    def to_internal_value(self, data):
        """Because we allow template ID string values, where
        serializers normally expect a dict
        """
        return super(URLTemplateSerializer, self).to_internal_value(
            _convert_template_id_to_dict(data))

    def get_write_serializer(self):
        return TemplateSerializer

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset


class TemplateSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Template
        fields = _template_serializer_fields

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
            view_name='template-detail',
            lookup_field='uuid')
    _template_id = serializers.CharField(write_only=True, required=False)
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(format='iso-8601', required=False)
    command = serializers.CharField(required=False)
    comments = serializers.CharField(required=False)
    import_comments = serializers.CharField(required=False)
    imported_from_url = serializers.CharField(required=False)
    is_leaf = serializers.BooleanField(required=False)
    interpreter = serializers.CharField(required=False)
    environment = serializers.JSONField(required=False)
    resources = serializers.JSONField(required=False)
    inputs = TemplateInputSerializer(many=True, required=False)
    # Fixed inputs are deprecated
    fixed_inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
    outputs  = serializers.JSONField(required=False)
    steps = URLTemplateSerializer(many=True, required=False)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset\
            .prefetch_related('steps')\
            .prefetch_related('inputs')\
            .prefetch_related('inputs__data_node')

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

        templates = []
        inputs = []
        m2m_relationships = []
        preexisting_templates = []

        self._create_unsaved_models(
            [copy.deepcopy(self.initial_data),], templates, inputs,
            m2m_relationships, preexisting_templates)

        root_uuid = templates[0].uuid

        templates = Template.objects.bulk_create(templates)
        templates = self._reload(Template, templates)
        templates = [template for template in templates]
        templates.extend(preexisting_templates)

        # Refresh unsaved objects with their saved counterparts
        self._match_and_update_by_uuid(inputs, 'template', templates)
        self._match_and_update_by_uuid(m2m_relationships, 'parent_template', templates)
        self._match_and_update_by_uuid(m2m_relationships, 'child_template', templates)

        TemplateInput.objects.bulk_create(inputs)
        TemplateMembership.objects.bulk_create(m2m_relationships)

        root_template = filter(lambda t: t.uuid==root_uuid, templates)
        return root_template[0]

    def _match_and_update_by_uuid(self, unsaved_models, field, saved_models):
        for unsaved_model in unsaved_models:
            uuid = getattr(unsaved_model, field).uuid
            match = filter(lambda m: m.uuid==uuid, saved_models)
            assert len(match) == 1
            setattr(unsaved_model, field, match[0])
    
    def _reload(self, ModelClass, models):
        # bulk_create doesn't give PK's, so we reload the models by uuid
        uuids = [model.uuid for model in models]

        # sort by id to preserve order, then verify
        models = ModelClass.objects.filter(uuid__in=uuids)
        return models
    
    def _lookup_by_id(self, template_id):
        matches = Template.filter_by_name_or_id_or_hash(template_id)
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
    
    def _create_unsaved_models(
            self,
            child_templates_data,
            template_models,
            input_models,
            m2m_relationship_models,
            preexisting_templates,
            parent_model=None):

        for template_data in child_templates_data:
            if isinstance(template_data, (unicode, str)):
                serializer = TemplateSerializer(
                    data=template_data)
                serializer.is_valid(raise_exception=True)
                template = serializer.save()
                preexisting_templates.append(template)
                # This step already exists. Just link to the parent
                if parent_model:
                    m2m_relationship_models.append(
                        TemplateMembership(
                            parent_template=parent_model,
                            child_template=template))
                continue

            # To be processed by recursion
            grandchildren = template_data.pop('steps', [])

            # Set defaults and inferred values
            if template_data.get('is_leaf') is None:
                template_data['is_leaf'] = not grandchildren
            if template_data['is_leaf']:
                _set_leaf_template_defaults(template_data)
            if not template_data.get('imported'):
                template_data['imported'] = bool(
                    template_data.get('imported_from_url'))

            inputs = template_data.pop('inputs', [])
            fixed_inputs = template_data.pop('fixed_inputs', [])
            inputs.extend(fixed_inputs)

            template = Template(**template_data)
            template_models.append(template)

            for input_data in inputs:
                input_data['template'] = template
                if template.is_leaf:
                    _set_leaf_input_defaults(input_data)
                if input_data.get('data'):
                    s = DataNodeSerializer(
                        data=input_data.pop('data'),
                        context={'type': input_data.get('type')}
                    )
                    s.is_valid(raise_exception=True)
                    input_data['data_node'] = s.save()
                input_models.append(TemplateInput(**input_data))

            if parent_model:
                m2m_relationship_models.append(
                    TemplateMembership(
                        parent_template=parent_model,
                        child_template=template))

            if grandchildren:
                self._create_unsaved_models(
                    grandchildren,
                    template_models,
                    input_models,
                    m2m_relationship_models,
                    preexisting_templates,
                    parent_model=template)


class SummaryTemplateSerializer(TemplateSerializer):

    #readable fields
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
            view_name='template-detail',
            lookup_field='uuid')
    name = serializers.CharField(required=False)
    md5 = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(format='iso-8601')
    is_leaf = serializers.BooleanField(required=False)
    steps = RecursiveField(many=True, required=False)

    # write-only fields
    _template_id = serializers.CharField(write_only=True, required=False)
    command = serializers.CharField(required=False, write_only=True)
    comments = serializers.CharField(required=False, write_only=True)
    import_comments = serializers.CharField(required=False, write_only=True)
    imported_from_url = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
    # Fixed inputs are deprecated
    fixed_inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
    outputs  = serializers.JSONField(required=False, write_only=True)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset\
            .prefetch_related('steps')\
            .prefetch_related('steps__steps')\
            .prefetch_related('steps__steps__steps')\
            .prefetch_related('steps__steps__steps__steps')\
            .prefetch_related('steps__steps__steps__steps__steps')\
            .prefetch_related('steps__steps__steps__steps__steps__'\
                              'steps')\
            .prefetch_related('steps__steps__steps__steps__steps__'\
                              'steps__steps')\
            .prefetch_related('steps__steps__steps__steps__steps__'\
                              'steps__steps__steps')\
            .prefetch_related('steps__steps__steps__steps__steps__'\
                              'steps__steps__steps__steps')\
            .prefetch_related('steps__steps__steps__steps__steps__'\
                              'steps__steps__steps__steps__steps')
            # Warning! This will break down with more than 11 levels
