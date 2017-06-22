from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rest_framework import serializers


def _get_class_from_string(kls):
    try:
        if issubclass(kls, serializers.Serializer):
            return kls
    except TypeError:
        pass

    # Get class from string
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

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


class SuperclassModelSerializer(serializers.HyperlinkedModelSerializer):
    """This class helps to ser/deserialize a base model with
    several subclasses. It selects the correctbclass serializer
    and delegates critical functions to it.
    """

    def _get_subclass_serializer_class(self, type):
        raise Exception('override needed')

    def _get_subclass_field(self, type):
        raise Exception('override needed')

    def validate(self, data):
        # This is critical to validating data against the SubclassSerializer
        if not hasattr(self, 'initial_data'):
            # No further validation possible if called in a mode without
            # initial data, because required fields may be lost
            return data
        type = self._get_type(data=data)
        # If this is an update, data may not have 'type'.
        # Not possible to validate here
        if type is None:
            return data
        SubclassSerializer \
            = self._get_subclass_serializer_class(type)
        serializer = SubclassSerializer(
            data=self.initial_data,
            context=self.context)
        serializer.is_valid(raise_exception=True)
        return data

    def create(self, validated_data):
        type = self._get_type(data=validated_data)
        SubclassSerializer \
            = self._get_subclass_serializer_class(type)
        serializer = SubclassSerializer(
            data=self.initial_data,
            context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def update(self, instance, validated_data):
        type = self._get_type(instance=instance)
        SubclassSerializer \
            = self._get_subclass_serializer_class(type)
        serializer = SubclassSerializer(
            instance,
            data=self.initial_data,
            context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict. It may be missing data in fields
            # that are on the subclass but not on the superclass, so we go
            # back to initial_data.
            type = self._get_type(data=instance)
            SubclassSerializer = self._get_subclass_serializer_class(
                type)
            serializer = SubclassSerializer(data=self.initial_data,
                                            context=self.context)
            return super(self.__class__, serializer).to_representation(
                self.initial_data)
        else:
            assert isinstance(instance, self.Meta.model)
            # Execute "to_representation" on the correct subclass serializer
            type = self._get_type(instance=instance)
            SubclassSerializer = self._get_subclass_serializer_class(
                type)
            subclass_field = self._get_subclass_field(type)
            if subclass_field:
                try:
                    instance = getattr(instance, subclass_field)
                except ObjectDoesNotExist:
                    pass
            serializer = SubclassSerializer(instance, context=self.context)
            if isinstance(serializer, self.__class__):
                return super(SuperclassModelSerializer, serializer)\
                    .to_representation(instance)
            else:
                return serializer.to_representation(instance)

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
