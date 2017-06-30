from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rest_framework import serializers


def strip_empty_values(data):
    return dict((k, v) for k, v in data.iteritems() if v not in [None, '', []])


class RecursiveField(serializers.Serializer):

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class ProxyWriteSerializer(serializers.HyperlinkedModelSerializer):
    """ProxyWriteSerializer acts as a pass-through for another serializer class
    for all the methods used in deserialization. 
    When is this useful? Consider that you have a recursive data type like 
    'Template' and a corresponding TemplateSerializer that handles nested data. 
    You may want a simplified serializer that renders just the URL of the child 
    objects but not the full nested structure. So you create a 
    TemplateURLSerializer that does not render the full nested structure. 
    That works fine for serialization, but it would be nice to support recursive 
    deserialization with the TemplateSerializer.
    Letting TemplateURLSerializer inherit from TemplateSerializer doesn't work
    because TemplateSerializer uses TemplateURLSerializer as a subfield, and this
    creates a dependency loop. This ProxyWriteSerializer is our work-around. 
    It lets TemplateURLSerializer send deserialization tasks to a TemplateSerializer
    while avoiding the dependency loop.
    """

    def get_target_serializer(self):
        raise Exception("Override get_target_serializer to "\
                        "return the target serializer class")

    def _get_serializer(self):
        if not hasattr(self, '_cached_serializer'):
            if self.instance is None:
                self._cached_serializer = self.get_target_serializer()(
                    data=self.initial_data, context=self.context)
            else:
                self._cached_serializer = self.get_target_serializer()(instance)
        return self._cached_serializer
    
    def is_valid(self, *args, **kwargs):
        return self._get_serializer().is_valid(*args, **kwargs)

    def create(self, *args, **kwargs):
        return self._get_serializer().create(*args, **kwargs)

    def update(self, *args, **kwargs):
        return self._get_serializer().update(*args, **kwargs)


class CreateWithParentModelSerializer(serializers.HyperlinkedModelSerializer):
    """Use this when a child has a required ForeignKey or OneToOne pointer 
    to the parent such that the parent has to be saved before creating 
    the child.

    Make sure this Mixin is listed before other inherited serializers
    so that the create method will override.
    """

    def create(self, validated_data):
        """ This is a standard method called indirectly by calling
        'save' on the serializer.

        This method expects the 'parent_field' and 'parent_instance' to
        be included in the Serializer context.
        """
        if self.context.get('parent_field') \
            and self.context.get('parent_instance'):
            validated_data.update({
                self.context.get('parent_field'):
                self.context.get('parent_instance')})
        return self.Meta.model.objects.create(**validated_data)


class ExpandableSerializerMixin(object):

    """ExpandableSerializer works with ExpandableViewSet to provide a custom
    level of rendering controlled by URL params. Objects may be rendered as
    "?expand", "?collapse", "?summary", or default.

    Serializers using the ExpandableSerializerMixin should implement these values
    to indicate the serializer classes to be used in each case:

    - DEFAULT_SERIALIZER
    - COLLAPSE_SERIALIZER
    - EXPAND_SERIALIZER
    - SUMMARY_SERIALIZER
    
    Each of those serializer classes should also
    implement this function to perform any calls to
    select_related and prefetch_related on the queryset:

    @classmethod
    _apply_prefetch(cls, queryset):
    ...

    Always inherit from ExpandableSerializerMixin before any other serializers, e.g.

    class ExpandableTaskSerializer(ExpandableSerializerMixin, TaskSerializer):
    ...

    """

    def to_representation(self, instance):
        Serializer = self._get_serializer_class(self.context)
        return Serializer(
            instance, context=self.context).to_representation(instance)

    @classmethod
    def apply_prefetch(cls, queryset, context):
	Serializer = cls._get_serializer_class(context)
        return Serializer._apply_prefetch(queryset)

    @classmethod
    def _get_serializer_class(cls, context):
        if context.get('collapse'):
            return cls.COLLAPSE_SERIALIZER
        elif context.get('expand'):
            return cls.EXPAND_SERIALIZER
	elif context.get('summary'):
            return cls.SUMMARY_SERIALIZER
        else:
            return cls.DEFAULT_SERIALIZER
