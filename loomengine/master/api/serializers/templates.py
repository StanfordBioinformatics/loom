import copy
import django.core.exceptions
from django.db.models import Prefetch
from jinja2.exceptions import UndefinedError
from rest_framework import serializers

from . import CreateWithParentModelSerializer, RecursiveField, \
    ProxyWriteSerializer, strip_empty_values
from .data_channels import DataChannelSerializer
from api import async
from api.models import DummyContext, render_from_template, render_string_or_list
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
    if data.get('outputs', []):
        for output in data.get('outputs', []):
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
    'import_comments',
    'imported_from_url',
    'is_leaf',
    'interpreter',
    'environment',
    'resources',
    'inputs',
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
    import_comments = serializers.CharField(required=False, write_only=True)
    imported_from_url = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
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
    import_comments = serializers.CharField(required=False)
    imported_from_url = serializers.CharField(required=False)
    is_leaf = serializers.BooleanField(required=False)
    interpreter = serializers.CharField(required=False)
    environment = serializers.JSONField(required=False)
    resources = serializers.JSONField(required=False)
    inputs = TemplateInputSerializer(many=True, required=False)
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

    def validate(self, data):
        # No validation if data is a template_ID. Only validate on create
        # to avoid an extra database hit.
        template_id = data.get('_template_id')
        if template_id:
            return data

        data_keys = self.initial_data.keys()
        serializer_keys = self.fields.keys()
        extra_fields = filter(lambda key: key not in serializer_keys, data_keys)
        if extra_fields:
            raise serializers.ValidationError(
                'Unrecognized fields %s' % extra_fields)

        # We have to use bulk_create for performance, so create all templates
        # before saving.
        # We need these to validate, and we'll cache them to reuse on create.
        self._unsaved_templates = []
        self._unsaved_inputs = []
        self._unsaved_m2m_relationships = []
        self._preexisting_templates = []
        template_data = copy.deepcopy(self.initial_data)
        self._create_unsaved_models(
            [template_data,], self._unsaved_templates,
            self._unsaved_inputs, self._unsaved_m2m_relationships,
            self._preexisting_templates)
        try:
            for model in self._unsaved_templates:
                model.full_clean()
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        self._validate_template_data(template_data, root=True)
        return data

    def _validate_template_data(self, data, root=False):
        self._validate_channels(data, root=root)
        self._validate_jinja_templates(data)
        for step in data.get('steps', []):
            self._validate_template_data(step)

    def _validate_jinja_templates(self, data):
        input_context = self._get_dummy_input_context(data)
        for output in data.get('outputs', []):
            if output.get('source'):
                self._validate_output_source(
                    output.get('source'), input_context)
        self._validate_command(data)

    def _validate_command(self, data):
        if not data.get('command'):
            return
        try:
            render_from_template(
                data.get('command'),
                self._get_dummy_full_context(data))
        except Exception as e:
            raise serializers.ValidationError({
                'command':
                'Error "%s" when parsing command "%s"' %
                (e, data.get('command'))})

    def _get_dummy_input_context(self, data):
        context = {}
        for input in data.get('inputs', []):
            if input.get('as_channel'):
                channel = input.get('as_channel')
            else:
                channel = input.get('channel')
            context[channel] = DummyContext('value')
        return context

    def _get_dummy_output_context(self, data):
        context = {}
	for output in data.get('outputs', []):
            if output.get('as_channel'):
                channel = output.get('as_channel')
            else:
                channel = output.get('channel')
            context[channel] = DummyContext('value')
        return context

    def _get_dummy_full_context(self, data):
        context = self._get_dummy_input_context(data)
        context.update(self._get_dummy_output_context(data))
        return context

    def _validate_output_source(self, output_source, input_context):
        try:
            render_from_template(
                output_source.get('filename'), input_context)
            render_string_or_list(
                output_source.get('filenames'),
                input_context)
            render_from_template(
                output_source.get('glob'), input_context)
        except UndefinedError as e:
            raise serializers.ValidationError({
                'source':
                'Error "%s" in output source "%s"' %
                (e, output_source)})

    def _validate_channels(self, data, root=False):
        self._validate_channels_no_duplicates(data)
        self._validate_channels_no_duplicate_sources(data)
        self._validate_channels_check_duplicate_inputs(data)
        self._validate_channels_valid_source(data, root=root)
        self._validate_input_dimensions(data)
        self._validate_no_cycles(data)

    def _validate_channels_no_duplicates(self, data):
        # Same channel name should never appear twice in a step
        visited_channels = set()
        for input in data.get('inputs', [])+data.get('outputs', []):
            channel = input.get('channel')
            if channel in visited_channels:
                raise serializers.ValidationError(
                    'Duplicate channel "%s" in template "%s"'
                    % (channel, data.get('name')))
            visited_channels.add(channel)

    def _validate_channels_no_duplicate_sources(self, data):
        # Same channel should not be both input of a step
        # and output of one of its children
        visited_channels = set()
        for input in data.get('inputs', []):
            channel=input.get('channel')
            if channel in visited_channels:
                raise serializers.ValidationError(
                    'Duplicate source channel "%s" in template "%s"'
                    % (channel, data.get('name')))
            visited_channels.add(channel)
        for step in data.get('steps', []):
            for output in step.get('outputs', []):
                channel = output.get('channel')
                if channel in visited_channels:
                    raise serializers.ValidationError(
                        'Duplicate source channel "%s" in template "%s"'
                        % (channel, data.get('name')))
                visited_channels.add(channel)

    def _validate_channels_check_duplicate_inputs(self, data):
        # If two siblings have the same channel, the channel must have a source,
        # either on the parent or on a sibling's output.
        sources = set()
        for input in data.get('inputs', []):
            sources.add(input.get('channel'))
        for step in data.get('steps', []):
            for output in step.get('outputs', []):
                sources.add(output.get('channel'))
        child_inputs = set()
        for step in data.get('steps', []):
            for input in step.get('inputs', []):
                channel = input.get('channel')
                if channel in child_inputs and channel not in sources:
                    raise serializers.ValidationError(
                        'Because the input channel "%s" exists on multiple child '\
                        'steps, it must have a shared source' % channel)
                child_inputs.add(channel)

    def _validate_channels_valid_source(self, data, root=False):
        if data.get('is_leaf') or data.get('_template_id'):
            # _template_id field indicates that this is a preexisting template
            # that should already be validated. Nested children are not loaded,
            # so cannot re-validate.
            # is_leaf indicates no children, so skip this validation step.
            return

        # Every channel should have a valid data source.
        # For inputs on root node of template, source can be given at runtime.
        sources = {}
        for input in data.get('inputs', []):
            sources[input.get('channel')] = input.get('type')
        for step in data.get('steps', []):
            for output in step.get('outputs', []):
                sources[output.get('channel')] = output.get('type')

        # Every output on a non-leaf node must have a source
        for output in data.get('outputs', []):
            if output.get('channel') in sources:
                if not output.get('type') == sources[output.get('channel')]:
                    raise serializers.ValidationError(
                        'Type mismatch on channel "%s", step "%s"'
                        % (output.get('channel'), step.get('name')))
            else:
                if not output.get('data'):
                    raise serializers.ValidationError(
                        'No source for output channel "%s" on step "%s".'
                        % (output.get('channel'), data.get('name')))

        # Every input on a child node must have a source
        for step in data.get('steps', []):
            for input in step.get('inputs', []):
                if input.get('channel') in sources:
                    if not input.get('type') == sources[input.get('channel')]:
                        raise serializers.ValidationError(
                            'Type mismatch on channel "%s", step "%s"'
                            % (input.get('channel'), step.get('name')))
                else:
                    # No external source, ok if it has fixed data.
                    if not input.get('data'):
                        raise serializers.ValidationError(
                            'No source for input channel "%s" on step "%s".'
                            % (input.get('channel'), step.get('name')))

    def _validate_input_dimensions(self, data):
        # Group settings only apply to leaf
        if not data.get('is_leaf'):
            return
        
        groups = {}
        for input in data.get('inputs', []):
            group = input.get('group')
            groups.setdefault(group, [])
            groups[group].append(input)
        for (group, inputs) in groups.iteritems():
            group_dimensions = None
            for input in inputs:
                if input.get('data'):
                    contents = input.get('data').get('contents')
                    dimensions = self._get_data_dimensions(contents, [])
                    if group_dimensions is None:
                        group_dimensions = dimensions
                    else:
                        if group_dimensions != dimensions:
                            raise serializers.ValidationError(
                                'Dimensions mismatch on input data '\
                                'in group "%s", step "%s"'
                                % (group, data.get('name')))

    def _get_data_dimensions(self, contents, path):
        if not isinstance(contents, list):
            return path
        else:
            paths = []
            for item in contents:
                paths.append(self._get_data_dimensions(item, copy.deepcopy(path)))
            return paths

    def _validate_no_cycles(self, data):
        CycleDetector(data.get('steps', [])).dfs()

    def create(self, validated_data):
        # If template_id is present, just look it up
        template_id = validated_data.get('_template_id')
        if template_id:
            return self._lookup_by_id(template_id)

        try:
            root_uuid = self._unsaved_templates[0].uuid

            bulk_templates = Template.objects.bulk_create(self._unsaved_templates)
            # self._new_templates includes pk's needed for cleanup on failure
            self._new_templates = self._reload(Template, bulk_templates)
            templates = [template for template in self._new_templates]
            templates.extend(self._preexisting_templates)

            # Refresh unsaved objects with their saved counterparts
            self._match_and_update_by_uuid(
                self._unsaved_inputs, 'template', templates)
            self._match_and_update_by_uuid(
                self._unsaved_m2m_relationships, 'parent_template', templates)
            self._match_and_update_by_uuid(
                self._unsaved_m2m_relationships, 'child_template', templates)

            # We can clean now that relationships have been defined.
            # Convert any model ValidationError
            # to serializer ValidationError to raise 400 http code.
            try:
                for instance in self._unsaved_inputs:
                    instance.full_clean()
                for instance in self._unsaved_m2m_relationships:
                    instance.full_clean()
            except django.core.exceptions.ValidationError as e:
                raise serializers.ValidationError(e.message_dict)

            TemplateInput.objects.bulk_create(self._unsaved_inputs)
            TemplateMembership.objects.bulk_create(self._unsaved_m2m_relationships)
                
            root_template = filter(lambda t: t.uuid==root_uuid, templates)
            assert len(root_template) == 1, '1 template should match uuid of root'
            return root_template[0]

        except:
            self._cleanup()
            raise

    def _cleanup(self):
        # Deleting the templates will cascade to delete
        # any TemplateInput or TemplateMembership
        if hasattr(self, '_new_templates'):
            self._new_templates.delete()

    def _match_and_update_by_uuid(self, unsaved_models, field, saved_models):
        for unsaved_model in unsaved_models:
            uuid = getattr(unsaved_model, field).uuid
            match = filter(lambda m: m.uuid==uuid, saved_models)
            assert len(match) == 1
            setattr(unsaved_model, field, match[0])
    
    def _reload(self, ModelClass, models):
        # bulk_create doesn't give PK's, so we have to reload the models.
        # We can look them up by uuid, which is also unique
        uuids = [model.uuid for model in models]
        models = ModelClass.objects.filter(uuid__in=uuids)
        return models
    
    def _lookup_by_id(self, template_id):
        matches = Template.filter_by_name_or_id_or_tag_or_hash(template_id)
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
        return matches.first()
    
    def _create_unsaved_models(
            self,
            child_templates_data,
            template_models,
            input_models,
            m2m_relationship_models,
            preexisting_templates,
            parent_model=None):

        for i in range(len(child_templates_data)):
            template_data = child_templates_data[i]
            if isinstance(template_data, (unicode, str)):
                # This is a reference to an existing template.
                template_id = template_data
                # Use the serializer to retrive the instance
                serializer = TemplateSerializer(
                    data=template_id)
                serializer.is_valid(raise_exception=True)
                # No new template created here, just a lookup
                template = serializer.save()
                preexisting_templates.append(template)
                # Link to parent if any
                if parent_model:
                    m2m_relationship_models.append(
                        TemplateMembership(
                            parent_template=parent_model,
                            child_template=template)
                    )
                    # Do not call full_clean yet.
                    # Relationships must be added first.
                # Replace the template reference with the full
                # template structure
                child_data = TemplateSerializer(
                    template, context=self.context).data
                child_data['_template_id'] = template_id
                child_templates_data[i] = child_data
                continue

            # Validate fields
            data_keys = template_data.keys()
            serializer_keys = self.fields.keys()
            extra_fields = filter(lambda key: key not in serializer_keys, data_keys)
            if extra_fields:
                raise serializers.ValidationError(
                    'Unrecognized fields %s' % extra_fields)

            # To be processed by recursion
            grandchildren = template_data.get('steps', [])

            # Set defaults and inferred values
            if template_data.get('is_leaf') is None:
                template_data['is_leaf'] = not grandchildren
            if template_data['is_leaf']:
                _set_leaf_template_defaults(template_data)
            if not template_data.get('imported'):
                template_data['imported'] = bool(
                    template_data.get('imported_from_url'))

            inputs = template_data.get('inputs', [])

            template_copy = copy.deepcopy(template_data)
            template_copy.pop('steps', None)
            template_copy.pop('inputs', None)
            template = Template(**template_copy)
            template_models.append(template)

            for input_data in inputs:
                if template.is_leaf:
                    _set_leaf_input_defaults(input_data)
                input_copy = copy.deepcopy(input_data)
                input_copy['template'] = template
                if input_copy.get('data'):
                    s = DataNodeSerializer(
                        data=input_copy.pop('data'),
                        context={'type': input_copy.get('type')}
                    )
                    s.is_valid(raise_exception=True)
                    input_copy['data_node'] = s.save()
                input_models.append(TemplateInput(**input_copy))

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
    import_comments = serializers.CharField(required=False, write_only=True)
    imported_from_url = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    inputs = TemplateInputSerializer(many=True, required=False, write_only=True)
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

class CycleDetector(object):

    def __init__(self, steps):
        self.white = []
        self.gray = []
        self.black = []
        self.edges = {}
        self.backtrack = {}
        for step in steps:
            assert step['name'] not in self.white
            self.white.append(step['name'])
            self.edges.setdefault(step['name'], [])
        for step in steps:
            for output in step.get('outputs', []):
                channel = output['channel']
                for dest in steps:
                    for input in dest.get('inputs', []):
                        if input.get('channel') == channel:
                            self.edges[step['name']].append(dest['name'])

    def dfs(self):
        while self.white:
            self._visit(self.white[0], None)

    def _visit(self, vertex, sender):
        if vertex in self.white:
            self.white.remove(vertex)
            self.gray.append(vertex)
            self.backtrack[vertex] = sender
            for neighbor in self.edges[vertex]:
                self._visit(neighbor, vertex)
            self.gray.remove(vertex)
            self.black.append(vertex)
        elif vertex in self.gray:
            # cycle detected
            cycle_steps = [vertex]
            next_step = sender
            while next_step != vertex and next_step != None:
                cycle_steps.append(next_step)
                next_step = self.backtrack[next_step]
            raise serializers.ValidationError(
                'Cycle detected in steps "%s"' % '", "'.join(cycle_steps))
        elif vertex in self.black:
            return

        
        
