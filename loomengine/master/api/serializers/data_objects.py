import copy
import django.core.exceptions
import jsonschema
import jsonschema.exceptions
from rest_framework import serializers

from api.models.data_objects import DataObject, FileResource

class DataValueSerializer(serializers.Field):

    def to_representation(self, value):
        data_type = value[0]
        data_value = value[1]
        if data_type != 'file':
            # For all non-file types, data_value is the value
            return data_value
        else:
            # For files, data_value is the FileResource instance
            return FileResourceSerializer(data_value).data

    def to_internal_value(self, data):
        return data

class DataObjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = DataObject
        fields = (
            'uuid',
            'url',
            'type',
            'datetime_created',
            'value',
        )

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='data-object-detail',
        lookup_field='uuid'
    )
    type = serializers.CharField(required=False) # Type can also come from context
    datetime_created = serializers.DateTimeField(required=False, format='iso-8601')
    value = DataValueSerializer(source='_value_info')

    def create(self, validated_data):
        value = validated_data.pop('_value_info')
        if not validated_data.get('type'):
            if self.context.get('type'):
                validated_data['type'] = self.context.get('type')
            else:
                raise serializers.ValidationError(
                    '"type" not found in "type" field or in context')
        if validated_data.get('type') != 'file':
            validated_data['data'] = {'value': value}
            return DataObjectSerializer\
                .Meta.model.objects.create(**validated_data)
        else:
            if not isinstance(value, dict):
                # If it's a string, treat it as a data_object identifier and
                # look it up. 
                data_objects = DataObject.filter_by_name_or_id(value)
                if data_objects.count() == 0:
                    raise serializers.ValidationError(
                        'No matching DataObject found for "%s"' % value)
                elif data_objects.count() > 1:
                    raise serializers.ValidationError(
                        'Multiple matching DataObjects found for "%s"' % value)
                return data_objects.first()
            else:
                # Otherwise, create new.
                data_object = self.Meta.model.objects.create(**validated_data)

                # If file belongs to TaskAttemptLogFile, make the connection
                log_file = self.context.get('task_attempt_log_file')
                if log_file:
                    log_file.setattrs_and_save_with_retries({
                        'data_object': data_object})

                try:
                    resource_init_args = copy.copy(value)
                    if self.context.get('task_attempt'):
                        resource_init_args['task_attempt'] = self.context.get(
                            'task_attempt')
                    resource_init_args['data_object'] = data_object
                    file_resource = FileResource.initialize(**resource_init_args)
                    return data_object
                except:
                    # Cleanup incomplete DataObject if we failed.
                    self._cleanup(data_object)
                    raise
                    
    def _cleanup(self, data_object):
        try:
            log_file = data_object.task_attempt_log_file
            log_file.data_object=None
            log_file.save()
        except django.core.exceptions.ObjectDoesNotExist:
            pass
        data_object.delete()

    @classmethod
    def get_select_related_list(cls):
        return ['file_resource']
                
    @classmethod
    def apply_prefetch(cls, queryset):
        for select_string in cls.get_select_related_list():
            queryset = queryset.select_related(select_string)
        return queryset


class FileResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileResource
        fields = (
            'filename',
            'file_url',
            'md5',
            'import_comments',
            'imported_from_url',
            'upload_status',
            'source_type'
        )
        
    filename = serializers.CharField()
    file_url = serializers.CharField(required=False)
    md5 = serializers.CharField()
    import_comments = serializers.CharField(required=False)
    imported_from_url = serializers.CharField(required=False)
    upload_status = serializers.ChoiceField(choices=FileResource.UPLOAD_STATUS_CHOICES,
                                            required=False)
    source_type = serializers.ChoiceField(choices=FileResource.SOURCE_TYPE_CHOICES,
                                          required=False)
        
class DataObjectUpdateSerializer(DataObjectSerializer):

    # Override to make all fields except value read-only
    uuid = serializers.UUIDField(read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='data-object-detail',
        lookup_field='uuid'
    )
    type = serializers.CharField(read_only=True)
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')

    def update(self, instance, validated_data):
        # The only time a DataObject should be updated by the client
        # is to change upload_status of a file.
        value_data = validated_data.get('_value_info')
        if value_data:
            if not instance.type == 'file':
                raise serializers.ValidationError(
                    'Updating value is not allowed on DataObject '\
                    'with type "%s"' % instance.type)
            if not instance.value:
                raise serializers.ValidationError(
                    "Failed to update DataObject because file value are missing")
            instance.value.upload_status = value_data.get('upload_status')
            try:
                instance.value.save()
            except django.core.exceptions.ValidationError as e:
                raise serializers.ValidationError(e.messages)
        return instance
