import copy
from rest_framework import serializers
from django.apps import AppConfig
from django.core.exceptions import ObjectDoesNotExist
from django.apps import AppConfig

_POLYMORPHIC_TYPE_FIELD = 'polymorphic_ctype'

def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

class MagicSerializer(serializers.ModelSerializer):
    """This class supplements the features of django-rest-framework
    and django-polymorphic to handle serialization/deserialization of
    nested models with polymorphic (multitable inheritance) relationships.
    It implements the following features:
      1. Extend DRF serializers to support creation and update with nested models
      2. When creating a model from serialized data, select the best subclass model 
         to use in a polymorphic relationship. Selection is based on whether model 
         fields match keys in input data. You can also explicitly select the class
         using the "_class" field in the data to be deserialized.
    """

    def create(self, validated_data):
        # Instead of using "self" to serialize, see if we should use the serializer for
        # a subclass of the current model instead.
        # If not, this call returns "self" as "serializer", meaning the current model is
        # the best match.
        serializer = self._select_subclass_serializer_by_data(self.initial_data)

        if serializer is self:
            # No need to use subclass, proceed with serialization
            validated_data_with_children = self._create_children(validated_data)
            return self.Meta.model.objects.create(**validated_data_with_children)
        
        else:
            # A subclass model matches the data better than the current model.
            # Defer deserialization to the serializer of the subclass.
            if not serializer.is_valid():
                raise Exception("Invalid data for model %s: %s" %
                                (serializer.Meta.model.__name__, serializer.initial_data))
            # Calling "save" will trigger the "create" method on the new serializer
            return serializer.save()

    def _create_children(self, validated_data):
        validated_data_with_children = copy.deepcopy(validated_data)
        # For models with nested children, handle that serialization here:
        if hasattr(self.Meta, 'nested_foreign_key_serializers'):
            for field_name, ChildSerializer in self.Meta.nested_foreign_key_serializers.iteritems():
                ChildSerializer = get_class(ChildSerializer)
                data = self.initial_data.get(field_name)
                if data:
                    child_serializer = ChildSerializer(data=data)
                    child_serializer.is_valid()
                    model = child_serializer.save()

                    # Replace raw data for child with model instance
                    validated_data_with_children[field_name] = model
        if hasattr(self.Meta, 'nested_many_to_many_serializers'):
            for field_name, ChildSerializer in self.Meta.nested_many_to_many_serializers.iteritems():
                ChildSerializer = get_class(ChildSerializer)
                if initial_data.get(field_name):
                    children = []
                    for data in initial_data.get(field_name):
                        child_serializer = ChildSerializer(data=data)
                        child_serializer.is_valid()
                        children.append(child_serializer.save())
                    validated_data_with_children[field_name] = children
        return validated_data_with_children

    def _select_subclass_serializer_by_data(self, data):
        """For a given set of data to be deserialized, and for the model class associated with
        the current serializer (self), determine whether this model or one of its subclass
        models is the best match for the data, and return the serializer associated with
        the matching model class
        """

        # If not polymorphic, keep the current model
        if not hasattr(self.Meta, 'subclass_serializers'):
            return self

        # Check if the model class is given explicitly in the data
        _class = data.get('_class')
        if _class is not None:
            if self.Meta.model.__name__ == _class:
                # Current model matches the class specified
                return self
            else:
                # Look for matches in the subclasses
                matching_serializers = filter(lambda s: s.Meta.model.__name__==_class, self.Meta.subclass_serializers.values())

        # Class is not explicitly specified, so we try to infer it from the data.

        # If all keys in the data match fields on the current model class, keep the current class.
        elif self._do_all_fields_match(self.Meta.model, data.keys()):
            return self

        # Otherwise select subclass model classes whose fields match all keys in the data
        else:
            matching_serializers = []
            for SubclassSerializer in self.Meta.subclass_serializers.values():
                SubclassSerializer = get_class(SubclassSerializer)
                if self._do_all_fields_match(SubclassSerializer.Meta.model, data.keys()):
                    matching_serializers.append(SubclassSerializer)

        # Verify just one match.
        if len(matching_serializers) == 0:
            raise Exception("Neither model %s nor its subclasses match the data given: %s"
                            % self.Meta.model.__name__, data)
        elif len(matching_serializers) > 1:
            raise Exception("Multiple subclasses (%s) of model %s match the input data: %s"
                            % (','.join([s.Meta.model.__name__ for s in matching_serializers]),
                               self.Meta.model.__name__, data))

        # Since we found a better matching subclass model class, substitute its serializer for the current one
        SubclassSerializer = matching_serializers[0]
        return SubclassSerializer(data=data, context=self.context)

    def _do_all_fields_match(self, model, fields):
        # All values in 'fields' can be found as fields on the model class
        return set(fields).issubset(set(model._meta.get_all_field_names()))

    def update(self, instance, validated_data):
        # Instead of using "self" to serialize, see if we should use the serializer for
        # a subclass of the current model class
        # If not, this call returns "self" as "serializer", meaning the current model is
        # the best match.
        serializer = self._select_subclass_serializer_by_model_instance()

        if serializer is self:
            # No need to use subclass, proceed with serialization for update
            validated_data_with_children = self._update_children(validated_data)

            for field_name, field_data in validated_data_with_children.iteritems():
                setattr(instance, field_name, field_data)
            instance.save()
            return instance
        
        else:
            # A subclass model exists. Defer deserialization to the serializer of the subclass.
            if not serializer.is_valid():
                raise Exception("Invalid data for model %s: %s" %
                                (serializer.Meta.model.__name__, serializer.instance))
            # Calling "save" will trigger the "create" method on the new serializer
            return serializer.save()

    def _update_children(self, validated_data):
        validated_data_with_children = copy.deepcopy(validated_data)
        # For models with nested children, handle that serialization here:
        if hasattr(self.Meta, 'nested_foreign_key_serializers'):
            for field_name, ChildSerializer in self.Meta.nested_foreign_key_serializers.iteritems():
                data = self.initial_data.get(field_name)
                ChildSerializer = get_class(ChildSerializer)
                try:
                    child_instance = getattr(self.instance, field_name)
                except ObjectDoesNotExist:
                    child_instance = None
                if data:
                    if child_instance:
                        # Update the existing child instance
                        child_serializer = ChildSerializer(child_instance, data=data, partial=True)
                    else:
                        # Create a new child instance
                        child_serializer = ChildSerializer(data=data)

                    if not child_serializer.is_valid():
                        raise Exception("Invalid data. Error messages: %s" % child_serializer.errors)

                    model = child_serializer.save()

                    # Replace raw data for child with model instance
                    validated_data_with_children[field_name] = model

        return validated_data_with_children

    def _select_subclass_serializer_by_model_instance(self):

        # If not polymorphic, keep the current model instance
        if not hasattr(self.Meta, 'subclass_serializers'):
            return self

        subclass_serializers=[]
        for (field, SubclassSerializer) in self.Meta.subclass_serializers:
            SubclassSerializer = get_class(SubclassSerializer)
            try:
                # If a model instance is assigned to 'field', it means there
                # is a subclass instance of the current model. If so, get the
                # Serializer for the subclass model instance
                subclass_instance = getattr(self.instance, field)
                subclass_serializers.append(SubclassSerializer(subclass_instance, data=self.initial_data))
            except ObjectDoesNotExist:
                pass

        if len(subclass_serializers) == 1:
            # We found a matching subclass instance, so we'll return its serializer
            # to replace the current one
            return subclass_serializers[0]
        
        elif len(subclass_serializers) == 0:
            # Model instance is does not belong to any subclass. Continue with the current serializer
            return self
        
        else:
            # We expect at most 1 matching subclass, but let's
            # verify because this is not enforced by Django.
            raise Exception("Could not deserialize because the model instance to be updated has multiple "\
                            "subclass instances, and we don't know which one to update. %s" % self.instance)
