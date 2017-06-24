from rest_framework import serializers
from api.models.data_objects import DataObject, FileResource


class DataContentsSerializer(serializers.Field):

    def to_representation(self, value):
        data_type = value[0]
        data_contents = value[1]
        if data_type != 'file':
            # For all non-file types, data_value is the value
            return data_contents
        else:
            # For files, data_value is the FileResource instance
            return FileResourceSerializer(data_contents).data

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
            'contents',
        )

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='data-object-detail',
        lookup_field='uuid'
    )
    type = serializers.CharField(required=False) # Type can also come from context
    datetime_created = serializers.DateTimeField(required=False, format='iso-8601')
    contents = DataContentsSerializer(source='_contents_info')

    def create(self, validated_data):
        contents = validated_data.pop('_contents_info')
        if not validated_data.get('type'):
            if self.context.get('type'):
                validated_data['type'] = self.context.get('type')
            else:
                raise ValidationError('"type" not found in "type" field or in context')
        if validated_data.get('type') != 'file':
            validated_data['data'] = {'contents': contents}
            return DataObjectSerializer\
                .Meta.model.objects.create(**validated_data)
        else:
            data_object = self.Meta.model.objects.create(**validated_data)
            try:
                contents['data_object'] = data_object
                FileResource.initialize(**contents)
                return data_object
            except:
                # Cleanup
                data_object.delete()
                raise

    def update(self, instance, validated_data):
        # The only time a DataObject should be updated by the client
        # is to change upload_status of a file.
        if self.initial_data.get('contents') \
           and instance.type == 'file' \
           and instance.contents:
            upload_status = self.initial_data['contents'].get('upload_status')
            if upload_status:
                instance.contents.upload_status = upload_status
                instance.contents.save()
        return instance

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset.select_related('file_resource')


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
        
