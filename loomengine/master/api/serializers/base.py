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


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class CreateWithParentModelSerializer(serializers.ModelSerializer):
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


class UuidSerializer(object):

    """Renders only data object "uuid" for deferred lookup
    """

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict. It may be missing data in fields
            # that are on the subclass but not on the superclass, so we go
            # back to initial_data.
            return { 'uuid': instance.get('uuid') }
        else:
            assert isinstance(instance, self.Meta.model)
            # Execute "to_representation" on the correct subclass serializer
            return { 'uuid': instance.uuid }


class NameAndUuidSerializer(object):

    """Renders only data object "name" and "uuid" for deferred lookup
    """

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict. It may be missing data in fields
            # that are on the subclass but not on the superclass, so we go
            # back to initial_data.
            return { 'uuid': instance.get('uuid'),
                     'name': instance.get('name') }
        else:
            assert isinstance(instance, self.Meta.model)
            # Execute "to_representation" on the correct subclass serializer
            return { 'uuid': instance.uuid,
                     'name': instance.name }


class SuperclassModelSerializer(serializers.ModelSerializer):
    """This class helps to ser/deserialize a base model with
    several subclasses. It selects the correct subclass serializer
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
            serializer = SubclassSerializer(data=self.initial_data)
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
