from django.core.exceptions import ObjectDoesNotExist
from django.db import models
import rest_framework.serializers


def strip_empty_values(data):
    return dict((k, v) for k, v in data.iteritems() if v not in [None, '', []])


class RecursiveField(rest_framework.serializers.Serializer):

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class ProxyWriteSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """ProxyWriteSerializer acts as a pass-through for another serializer class
    for all the methods used in deserialization. 
    When is this useful? Consider that you have a recursive data type like 
    'Template' and a corresponding TemplateSerializer that handles nested data. 
    You may want a simplified serializer that renders just the URL of the child 
    objects but not the full nested structure. So you create a 
    URLTemplateSerializer that does not render the full nested structure. 
    That works fine for serialization, but it would be nice to support recursive 
    deserialization with the TemplateSerializer.
    Letting URLTemplateSerializer inherit from TemplateSerializer doesn't work
    because TemplateSerializer uses URLTemplateSerializer as a subfield, and this
    creates a dependency loop. This ProxyWriteSerializer is our work-around. 
    It lets URLTemplateSerializer send deserialization tasks to a TemplateSerializer
    while avoiding the dependency loop.
    """

    def get_write_serializer(self):
        raise Exception("Override get_write_serializer to "\
                        "return the target serializer class")

    def _get_serializer(self):
        if not hasattr(self, '_cached_serializer'):
            if self.instance is None:
                self._cached_serializer = self.get_write_serializer()(
                    data=self.initial_data, context=self.context)
            else:
                self._cached_serializer = self.get_write_serializer()(instance)
        return self._cached_serializer
    
    def is_valid(self, *args, **kwargs):
        return self._get_serializer().is_valid(*args, **kwargs)

    def create(self, *args, **kwargs):
        return self._get_serializer().create(*args, **kwargs)

    def update(self, *args, **kwargs):
        return self._get_serializer().update(*args, **kwargs)

    def save(self, *args, **kwargs):
        return self._get_serializer().save(*args, **kwargs)


class CreateWithParentModelSerializer(
        rest_framework.serializers.HyperlinkedModelSerializer):
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
        instance = self.Meta.model(**validated_data)
        instance.full_clean()
        instance.save()
        return instance


from .data_objects import *
from .data_nodes import *
from .labels import *
from .runs import *
from .tags import *
from .task_attempts import *
from .tasks import *
from .templates import *
from .users import *
