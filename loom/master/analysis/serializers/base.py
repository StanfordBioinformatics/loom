import copy
from rest_framework import serializers


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
        serializer = self._select_polymorphic_subclass_serializer(self.initial_data)

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
        if hasattr(self.Meta, 'nested_serializers'):
            for field_name, ChildSerializer in self.Meta.nested_serializers.iteritems():
                child_serializer = ChildSerializer(data=self.initial_data.get(field_name))
                child_serializer.is_valid()
                model = child_serializer.save()

                # Replace raw data for child with model instance
                validated_data_with_children[field_name] = model
        return validated_data_with_children

    def _select_polymorphic_subclass_serializer(self, data):
        """For a given set of data to be deserialized, and for the model associated with
        the current serializer (self), determine whether this model or one of its subclass
        models is the best match for the data, and return the serializer associated with
        the matching model
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
                matching_serializers = filter(lambda s: s.Meta.model.__name__==_class, self.Meta.subclass_serializers)

        # Class is not explicitly specified, so we try to infer it from the data.

        # If all keys in the data match fields on the current model, keep the current model.
        elif self._do_all_fields_match(self.Meta.model, data.keys()):
            return self

        # Otherwise select subclass models whose fields match all keys in the data
        else:
            matching_serializers = []
            for subclass_serializer in self.Meta.subclass_serializers:
                if self._do_all_fields_match(subclass_serializer.Meta.model, data.keys()):
                    matching_serializers.append(subclass_serializer)

        # Verify just one match.
        if len(matching_serializers) == 0:
            raise Exception("Neither model %s nor its subclasses match the data given: %s"
                            % self.Meta.model.__name__, data)
        elif len(matching_serializers) > 1:
            raise Exception("Multiple subclasses (%s) of model %s match the input data: %s"
                            % (','.join([s.Meta.model.__name__ for s in matching_serializers]),
                               self.Meta.model.__name__, data))

        # Since we found a better matching subclass model, substitute its serializer for the current one
        return matching_serializers[0](data=data, context=self.context)

    def _do_all_fields_match(self, model, fields):
        # All values in 'fields' can be found as fields on the model
        return set(fields).issubset(set(model._meta.get_all_field_names()))
