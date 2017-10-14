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

    def validate(self, data):
        # Use a copy to avoid modifying data
        datacopy = copy.deepcopy(data)

        # Type is required unless this is an update
        datacopy.setdefault('type', self.context.get('type'))
        if not datacopy.get('type') and not self.instance:
            raise serializers.ValidationError(
                'DataObject "type" not found in "type" field or in context')

        if datacopy['type'] == 'file':
            self._validate_file(datacopy)
        else:
            self._validate_nonfile(datacopy)

        return data

    def _validate_nonfile(self, data):
        value = data.pop('_value_info')
        data['data'] = {'value': value}
        self._cached_data_object = DataObjectSerializer\
            .Meta.model(**data)
        self._do_create_new_data_object=True
        try:
            self._cached_data_object.full_clean()
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return data

    def _validate_file(self, data):
        value = data.pop('_value_info')
        if not isinstance(value, dict):
            # If it's a string, treat it as a data_object identifier and
            # look it up.
            data_objects = DataObject.filter_by_name_or_id_or_tag_or_hash(value)
            if data_objects.count() == 0:
                raise serializers.ValidationError(
                    'No matching DataObject found for "%s"' % value)
            elif data_objects.count() > 1:
                raise serializers.ValidationError(
                    'Multiple matching DataObjects found for "%s"' % value)
            self._cached_data_object = data_objects.first()
            self._do_create_new_data_object = False
        else:
            # Otherwise, create new.
            self._cached_data_object = self.Meta.model(**data)
            self._do_create_new_data_object = True
            try:
                self._cached_data_object.full_clean()
            except django.core.exceptions.ValidationError as e:
                raise serializers.ValidationError(e.message_dict)
        return data

    def create(self, validated_data):
        if not self._do_create_new_data_object:
            return self._cached_data_object
        else:
            if self._cached_data_object.type == 'file':
                return self._create_file(validated_data)
            else:
                return self._create_nonfile(validated_data)

    def _create_nonfile(self, validated_data):
        data_object = self._cached_data_object
        if self._do_create_new_data_object:
            data_object.save()
            return data_object

    def _create_file(self, validated_data):
        value = validated_data.pop('_value_info')
        try:
            self._cached_data_object.save()
            # If file belongs to TaskAttemptLogFile, make the connection
            log_file = self.context.get('task_attempt_log_file')
            if log_file:
                log_file.setattrs_and_save_with_retries({
                    'data_object': self._cached_data_object})
            resource_init_args = copy.copy(value)
            if self.context.get('task_attempt'):
                resource_init_args['task_attempt'] = self.context.get(
                    'task_attempt')
            resource_init_args['data_object'] = self._cached_data_object
            file_resource = FileResource.initialize(**resource_init_args)
            try:
                file_resource.full_clean()
            except django.core.exceptions.ValidationError as e:
                raise serializers.ValidationError(e.message_dict)
            file_resource.save()
            return self._cached_data_object
        except Exception as e:
            self._cleanup(self._cached_data_object)
            raise

    def _cleanup(self, data_object):
        try:
            log_file = data_object.task_attempt_log_file
            log_file.setattrs_and_save_with_retries({
                'data_object': None})
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

    def validate(self, data):
        return data

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
                    "Failed to update DataObject because FileResource is missing")
            try:
                instance.value.setattrs_and_save_with_retries({
                    'upload_status': value_data.get('upload_status')})
            except django.core.exceptions.ValidationError as e:
                raise serializers.ValidationError(e.messages)
        return instance
