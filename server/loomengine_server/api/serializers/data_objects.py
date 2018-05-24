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


class URLDataObjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = DataObject
        fields = (
            'uuid',
            'url',
            'type',
            'datetime_created',
        )

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='data-object-detail',
        lookup_field='uuid'
    )
    type = serializers.CharField(required=False, write_only=True)
    datetime_created = serializers.DateTimeField(
        required=False, format='iso-8601', write_only=True)

    def validate(self, data):
        # Use a copy to avoid modifying data
        datacopy = copy.deepcopy(data)

        # Type is required unless this is an update
        datacopy.setdefault('type', self.context.get('type'))
        if not datacopy.get('type') and not self.instance:
            raise serializers.ValidationError(
                'DataObject "type" not found in "type" field or in context')

        if datacopy['type'] == 'file':
            self._validate_and_cache_file(datacopy)
        else:
            self._validate_and_cache_nonfile(datacopy)
        return data

    def _validate_and_cache_nonfile(self, data):
        value = data.get('_value_info')
        type = data.get('type')
        try:
            self._cached_data_object = DataObject.objects.get(
                uuid=data.get('uuid'))
            self._do_create_new_data_object=False
            self._verify_data_object_matches_data(self._cached_data_object, data)
            return data
        except DataObject.DoesNotExist:
            pass
        self._cached_data_object = DataObjectSerializer\
            .Meta.model.get_by_value(value, type)
        self._do_create_new_data_object=False # already saved
        try:
            self._cached_data_object.full_clean()
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return data

    def _validate_and_cache_file(self, data):
        value = data.get('_value_info')
        if value is not None and not isinstance(value, dict):
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
            if data.get('uuid'):
                try:
                    self._cached_data_object = DataObject.objects.get(
                        uuid=data.get('uuid'))
                    self._do_create_new_data_object=False
                    self._verify_data_object_matches_data(
                        self._cached_data_object, data)
                    return data
                except DataObject.DoesNotExist:
                    # Create new, with given UUID
                    data.pop('_value_info')
                    self._cached_data_object = self.Meta.model(**data)
                    self._do_create_new_data_object = True
            else:
                # Otherwise, create new.
                data.pop('_value_info')
                self._cached_data_object = self.Meta.model(**data)
                self._do_create_new_data_object = True
            try:
                self._cached_data_object.full_clean()
            except django.core.exceptions.ValidationError as e:
                raise serializers.ValidationError(e.message_dict)
        return data

    def _verify_data_object_matches_data(self, data_object, data):
        datetime_created = data.get('datetime_created')
        value = data.get('_value_info')
        type = data.get('type')
        if datetime_created and datetime_created != data_object.datetime_created:
            raise serializers.ValidationError(
                'datetime_created mismatch for DataObject "%s"' % data_object.uuid)
        if type and type != data_object.type:
            raise serializers.ValidationError(
                'type mismatch for DataObject "%s"' % data_object.uuid)
        if data_object.type == 'file':
            if value:
                try:
                    self._verify_file_resource_matches_data(data_object.value, value)
                except serializers.ValidationError as e:
                    raise serializers.ValidationError(
                        'Value mismatch for DataObject "%s"'
                        % data_object.uuid)
        else:
            if value and value != data_object.value:
                raise serializers.ValidationError(
                    'Value mismatch for DataObject "%s"' % data_object.uuid)

    def _verify_file_resource_matches_data(self, file_resource, data):
        filename = data.get('filename')
        md5 = data.get('md5')
        source_type = data.get('source_type')
        import_comments = data.get('import_comments')
        imported_from_url = data.get('imported_from_url')
        if filename and filename != file_resource.filename:
            raise serializers.ValidationError('filename mismatch')
        if md5 and md5 != file_resource.md5:
            raise serializers.ValidationError('md5 mismatch')
        if source_type and source_type != file_resource.source_type:
            raise serializers.ValidationError('source_type mismatch')
        if import_comments and import_comments != file_resource.import_comments:
            raise serializers.ValidationError('import_comments mismatch')
        if imported_from_url and imported_from_url != file_resource.imported_from_url:
            raise serializers.ValidationError('imported_from_url mismatch')
        # Do not check values file_url, upload_status, or link, since these
        # may vary between systems. when a file is re-imported.

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


class FileResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileResource
        fields = (
            'filename',
            'file_url',
            'file_relative_path',
            'md5',
            'import_comments',
            'imported_from_url',
            'upload_status',
            'source_type',
            'link'
        )
        
    filename = serializers.CharField()
    file_url = serializers.CharField(required=False)
    file_relative_path = serializers.CharField(required=False)
    md5 = serializers.CharField()
    import_comments = serializers.CharField(required=False)
    imported_from_url = serializers.CharField(required=False)
    upload_status = serializers.ChoiceField(choices=FileResource.UPLOAD_STATUS_CHOICES,
                                            required=False)
    source_type = serializers.ChoiceField(choices=FileResource.SOURCE_TYPE_CHOICES,
                                          required=False)
    link = serializers.BooleanField(required=False)



class DataObjectSerializer(URLDataObjectSerializer):

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
    value = DataValueSerializer(source='_value_info', required=False)


class UpdateDataObjectSerializer(DataObjectSerializer):

    # Override to make all fields except value read-only
    uuid = serializers.UUIDField(read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='data-object-detail',
        lookup_field='uuid'
    )
    type = serializers.CharField(read_only=True)
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    value = DataValueSerializer(source='_value_info', required=False)

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
