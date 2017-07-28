from api.models.tags import Tag
from api.models.templates import Template
from api.models.data_objects import DataObject
from api.models.runs import Run
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.templates import URLTemplateSerializer
from api.serializers.runs import URLRunSerializer
from rest_framework import serializers

def _convert_target_id_to_dict(data):
    # If data is a string instead of a dict value,
    # set that as _template_id
    if isinstance(data, (str, unicode)):
        return {'_target_id': data}
    else:
        return data

class TargetSerializer(serializers.Serializer):

    _target_id = serializers.CharField(write_only=True, required=False)

    def to_internal_value(self, data):
        """Because target may be an ID string value, where
        serializers normally expect a dict
        """
        return super(TargetSerializer, self).to_internal_value(
            _convert_target_id_to_dict(data))

    def create(self, validated_data):
        target_id = validated_data.get('_target_id')
        if not target_id:
            uuid = self.initial_data.get('uuid')
            if not uuid:
                raise serializers.ValidationError('Target identifier not found')
            target_id = '@%s' % uuid
        # Return model instance of DataObject, Template, or Run
        return self._lookup_by_id(target_id)

    def _lookup_by_id(self, target_id):
        template_matches = Template.filter_by_name_or_id_or_hash(target_id)
        file_matches = DataObject.filter_by_name_or_id_or_hash(target_id)
        # Hash is not allowed for runs, so search only if it is absent
        if '$' in target_id:
            run_matches = Run.objects.none()
        else:
            run_matches = Run.filter_by_name_or_id(target_id)

        if template_matches.count()+run_matches.count()+file_matches.count() < 1:
            raise serializers.ValidationError(
                'No target found that matches value "%s"' % target_id)
	elif template_matches.count()+run_matches.count()+file_matches.count() > 1:
            match_id_list = ['%s %s@%s' % ('file', match.name, match.uuid)
	                     for match in file_matches]
            match_id_list.extend(['%s %s@%s' % ('template', match.name, match.uuid)
	                          for match in template_matches])
            match_id_list.extend(['%s %s@%s' % ('run', match.name, match.uuid)
	                          for match in run_matches])
            match_id_string = ('", "'.join(match_id_list))
	    raise serializers.ValidationError(
		'Multiple targets were found matching value "%s": "%s". '\
                'Use a more precise identifier to select just one target.' % (
                    target_id, match_id_string))
        if file_matches.count() > 0:
            return file_matches.first()
        if template_matches.count() > 0:
            return template_matches.first()
        return run_matches.first()

    def to_representation(self, instance):
        if isinstance(instance, DataObject):
            return DataObjectSerializer(instance, context=self.context).data
        elif isinstance(instance, Template):
            return URLTemplateSerializer(instance, context=self.context).data
        elif isinstance(instance, Run):
            return URLRunSerializer(instance, context=self.context).data
        else:
            raise Exception('Tag target does not have a valid class: %s' % str(instance))


class TagSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Tag
        fields = ('id',
                  'name',
                  'type',
                  'target',
                  'datetime_created',
        )

    name = serializers.CharField(required=True)
    target = TargetSerializer(required=True)
    type = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(format='iso-8601', required=False)

    @classmethod
    def apply_prefetch(cls, queryset):
        queryset = queryset\
                   .select_related('file')\
                   .select_related('file__file_resource')\
                   .select_related('template')\
                   .select_related('run')
        return queryset

    def create(self, validated_data):
        target_data = validated_data.pop('target')

        s = TargetSerializer(data=target_data)
        s.is_valid(raise_exception=True)
        target = s.save()
        specified_type = validated_data.get('type')
        discovered_type = self.get_target_type(target)

        if specified_type and specified_type != discovered_type:
            raise serializers.ValidationError(
                'Type mismatch between tag and target')
        validated_data.update({
            'type': discovered_type,
            discovered_type: target})

        tag = Tag(**validated_data)
        tag.full_clean()
        tag.save()
        return tag

    def get_target_type(self, target):
        if isinstance(target, DataObject):
            return 'file'
        elif isinstance(target, Template):
            return 'template'
        elif isinstance(target, Run):
            return 'run'
        else:
            raise Exception('Tag target does not have a valid class: %s' % str(target))

    def to_representation(self, instance):
        representation = super(TagSerializer, self).to_representation(instance)
        type = instance.type
        target = getattr(instance, type)
        target_data = TargetSerializer(target, context=self.context).data
        representation.update({'target': target_data})
        return representation
