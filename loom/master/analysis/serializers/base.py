import copy
from django.apps import AppConfig
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rest_framework import serializers

from .exceptions import *


class NoCreateMixin(object):
    """For models that cannot be created directly.
    e.g. for children of a OneToMany relationship where the ForeignKey 
    to the parent is required, the parent serializer should create the
    children directly, and the child serializer is read-only.

    Make sure this Mixin is listed before other parent serializers
    so that the create method will override.
    """

    def create(self, validated_data):
        raise CreateNotAllowedError(self.Meta.model)


class NoUpdateMixin(object):
    """For models that should not be edited after creation. This only works 
    with simple scalar fields. For non-updatable models with children,
    write a custom update function. For example, see FileContentSerializer.

    Make sure this Mixin is listed before other parent serializers
    so that the update method will override.
    """

    def update(self, instance, validated_data):
        # This class should never be updated, so we verify
        # that the data is unchanged.
        for (key, value) in validated_data.iteritems():
            if not getattr(instance, key) == value:
                raise UpdateNotAllowedError(instance)
        return instance


class SuperclassModelSerializer(serializers.ModelSerializer):
    """This class helps to ser/deserialize a base model with
    several subclasses.
    """

    # Override with {'subclassfieldname': Serializer}, for example:
    #
    # subclass_serializers = {'childone': ChildOneSerializer,
    #                         'childtwo': ChildTwoSerializer}
    #
    subclass_serializers = {}

    def create(self, validated_data):
        SubclassSerializer \
            = self._select_subclass_serializer_by_data(
                self.initial_data)
        serializer = SubclassSerializer(
            data=self.initial_data,
            context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def update(self, instance, validated_data):
        SubclassSerializer \
            = self._select_subclass_serializer_by_data(
                self.initial_data)
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
            SubclassSerializer = self._select_subclass_serializer_by_data(
                self.initial_data)
            serializer = SubclassSerializer(data=self.initial_data)
            return super(serializer.__class__, serializer).to_representation(
                self.initial_data)
        else:
            assert isinstance(instance, self.Meta.model)
            # Execute "to_representation" on the correct subclass serializer
            SubclassSerializer \
                = self._select_subclass_serializer_by_model_instance(instance)
            serializer = SubclassSerializer(instance, context=self.context)
            return super(serializer.__class__, serializer).to_representation(
                instance)

    def _select_subclass_serializer_by_data(self, data):
        """For a given set of data to be deserialized, and for the model class
        associated with the current serializer (self), determine whether this 
        model or one of its subclass models is the best match for the data, 
        and return the serializer associated with the matching model class
        """

        matching_serializers = []
        for Serializer in self.subclass_serializers.values():
            if self._do_all_fields_match(Serializer.Meta.model, data.keys()):
                matching_serializers.append(Serializer)

        # Verify just one match.
        if len(matching_serializers) == 0:
            raise serializers.ValidationError(
                "Serializer %s does not have any subclasses matching "\
                "the data given: %s" % (
                    self.__class__.__name__, data))
        elif len(matching_serializers) > 1:
            raise serializers.ValidationError(
                "Multiple subclasses (%s) of serialier %s match "\
                "the input data: %s" % (','.join(
                    [s.Meta.model.__name__ for s in matching_serializers]),
                                        self.__class__.__name__, data))

        # Since we found a better matching subclass model class,
        # substitute its serializer for the current one
        return matching_serializers[0]

    def _select_subclass_serializer_by_model_instance(
            self, instance, data=None):
        matching_serializers=[]
        for (field, Serializer) in self.subclass_serializers.iteritems():
            try:
                # If a model instance is assigned to 'field', it means there
                # is a subclass instance of the current model. If so, get the
                # Serializer for the subclass model instance
                #
                subclass_instance = getattr(instance, field)
                matching_serializers.append(Serializer)
            except ObjectDoesNotExist:
                pass

        if len(matching_serializers) == 1:
            # Good, we have one match.
            return matching_serializers[0]
        elif len(matching_serializers) == 0:
            raise serializers.ValidationError(
                "Could not deserialize because "\
                "the data did not match any subclass")
        else:
            # We expect at most 1 matching subclass,
            # but this is not enforced by Django
            raise serializers.ValidationError(
                "Could not deserialize because the model instance to be "\
                "updated has multiple subclass instances, and we don't know "\
                "which one to update. %s" % instance)

    def _do_all_fields_match(self, model, fields):
        # All values in 'fields' can be found as fields on the model class
        return set(fields).issubset(set(model._meta.get_all_field_names()))
