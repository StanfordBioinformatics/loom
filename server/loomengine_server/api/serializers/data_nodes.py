import copy
from django.db import models
import jsonschema
from rest_framework import serializers

from .data_objects import DataObjectSerializer, URLDataObjectSerializer
from api.models.data_nodes import DataNode
from api.models.data_objects import DataObject
from api.models.validators import data_node_schema


class URLDataNodeSerializer(serializers.HyperlinkedModelSerializer):

    BLANK_NODE_VALUE = None
    EMPTY_BRANCH_VALUE = []

    # Serializes/deserializers a tree of DataObjects.
    # Input is a string, integer, float, boolean, or dict representation 
    # of a DataObject, or a list of [lists of]^n these representations.
    # Output is a dict or list of [lists of]^n dicts.

    # 'contents' is write_only so that HyperlinkedModelSerializer will skip.
    # We render 'contents' in a custom way in to_representation
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='data-node-detail',
        lookup_field='uuid'
    )
    contents = serializers.JSONField(write_only=True)

    class Meta:
        model = DataNode
        fields = ('uuid', 'url', 'contents',)

    def create(self, validated_data):
        type = self.context.get('type')
        if not type:
            raise Exception('data type must be set in serializer context')
        contents = self.initial_data.get('contents')
        if contents is None:
            raise Exception('No data contents. Cannot create DataNode')
        data_node = self._create_data_node_from_data_objects(
            contents, type)
        return data_node

    def is_valid(self, **kwargs):
        return super(URLDataNodeSerializer, self).is_valid(**kwargs)

    def validate_contents(self, value):
        try:
            jsonschema.validate(value, data_node_schema)
        except jsonschema.exceptions.ValidationError:
            raise serializers.ValidationError(
                "Data contents must be a string, number, boolean, or object, a list "\
                "of these, or nested lists of these." \
                "Invalid value: '%s'" % value)
        try:
            self._validate_uniform_height(value)
        except serializers.ValidationError:
            raise serializers.ValidationError(
                "Nested data contents must have uniform height. '\
                'Invalid value: '%s'" % value)
        return value

    def _validate_uniform_height(self, contents):
        if not isinstance(contents, (list, tuple)):
            # This is a data object, not a list. Height is 1.
            return 1

        # Gather heights of child branches with recursion
        heightlist = []
        for item in contents:
            heightlist.append(self._validate_uniform_height(item))

        # Make sure min(depths) and max(depths) are equal.
        # Ignore "None" in validation since this represents a 
        # missing branch of unknown depth
        heights = set(heightlist)
        if len(heights) == 0:
            # No data objects.
            # Height of absent objects is 1, height of list is 2
            return 2
        if None in heights and len(heights) == 1:
            # No non-missing branches. Indeterminate height, so return None
            return None

        # Ignoring "None", check the height of what's left.
        try:
            heights.remove(None)
        except:
            pass
        minheight = min(heights)
        maxheight = max(heights)
        if minheight != maxheight:
            # Non-uniform height. Invalid contents.
            raise serializers.ValidationError('Height is not uniform')

        # Add 1 for the current level
        return minheight + 1

    def _create_data_node_from_data_objects(self, contents, data_type):
        data_node = DataNode(type=data_type)
        data_node.full_clean()
        data_node.save()
        self._add_data_objects(data_node, contents, data_type)
        return data_node

    def _add_data_objects(self, data_node, contents, data_type):
        path = []
        self._extend_all_paths_and_add_data_at_leaves(
            data_node, contents, path, data_type)

    def _extend_all_paths_and_add_data_at_leaves(
            self, data_node, contents, path, data_type):
        # Recursive function that extends 'path' until reaching a leaf node,
        # where data is finally added.
        # 'path' is the partial path to some intermediate
        # node, while 'contents' is the representation of all branches and 
        # leaves beyond that path.
        # For example, given path (0,2) and contents [['10','20']['30','40']],
        # the function places all data under (0,2) and ignores the other
        # root-level branch (1,2).
        # The function adds these four data objects at
        # their corresponding paths:
        # 10 at [(0,2), (0,2), (0,2)]
        # 20 at [(0,2), (0,2), (1,2)]
        # 30 at [(0,2), (1,2), (0,2)]
        # 40 at [(0,2), (1,2), (1,2)]
        if not isinstance(contents, list):
            if isinstance(contents, dict):
                s = DataObjectSerializer(data=contents, context=self.context)
                s.is_valid(raise_exception=True)
                data_object = s.save()
            else:
                data_object = DataObject.get_by_value(
                    contents,
                    data_type)
            data_node.add_data_object(path, data_object)
            return
        elif len(contents) == 0:
            # An empty list represents a node of degree 0
            data_node.setattrs_and_save_with_retries({
                'degree': 0})
        else:
            for i in range(len(contents)):
                path_i = copy.deepcopy(path)
                path_i.append((i, len(contents)))
                self._extend_all_paths_and_add_data_at_leaves(
                    data_node, contents[i], path_i, data_type)


class DataNodeSerializer(URLDataNodeSerializer):

    EXPAND = False

    contents = serializers.JSONField()

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            return super(self.__class__, self).to_representation(
                self.initial_data)
        else:
            assert isinstance(instance, DataNode)
            instance = self._apply_prefetch_to_instance(instance)
            representation = super(
                URLDataNodeSerializer, self).to_representation(instance)
            representation.update({
                'contents': self._data_node_to_data_struct(instance)})
            return representation

    def _data_node_to_data_struct(self, data_node):
        if data_node._is_blank_node():
            return self.BLANK_NODE_VALUE
        elif data_node._is_empty_branch():
            return self.EMPTY_BRANCH_VALUE
        if data_node.is_leaf:
            if self.EXPAND:
                s = DataObjectSerializer(data_node.data_object, context=self.context)
            else:
                s = URLDataObjectSerializer(data_node.data_object, context=self.context)
            return s.data
        else:
            contents = [self.BLANK_NODE_VALUE] * data_node.degree
            for child in data_node.children.all():
                contents[child.index] = self._data_node_to_data_struct(child)
            return contents
 
    def _apply_prefetch_to_instance(self, instance):
        queryset = DataNode\
                   .objects\
                   .filter(uuid=instance.uuid)\
                   .prefetch_related('children')\
                   .prefetch_related('children__children')\
                   .prefetch_related('children__children__children')\
                   .prefetch_related('children__children__children__children')\
                   .prefetch_related('children__children__children__children__children')                   .prefetch_related(
                       'children__children__children__children__children__children')\
                   .prefetch_related('children__children__children__children__'\
                                     'children__children__children__children')\
                   .prefetch_related(
                       'children__children__children__children__children__'\
                       'children__children__children__children')\
                   .prefetch_related(
                       'children__children__children__children__children__'\
                       'children__children__children__children__children')
        instance = queryset[0]
        node_list = self._flatten_nodes(instance)
        queryset = DataNode.objects.filter(uuid__in=[n.uuid for n in node_list])\
            .prefetch_related('data_object')
        if self.EXPAND:
            queryset = queryset.prefetch_related('data_object__file_resource')
        data_nodes = [node for node in queryset]
        instance = self._replace_nodes(instance, data_nodes)
        return instance

    def _flatten_nodes(self, node, node_list=None):
        if node_list == None:
            node_list = []
        node_list.append(node)
        for child in node.children.all():
            self._flatten_nodes(child, node_list)
        return node_list

    def _replace_nodes(self, old_instance, data_nodes):
        old_uuid = old_instance.uuid
        matches = filter(lambda n: n.uuid==old_uuid, data_nodes)
        assert len(matches) == 1, 'no unique match found'
        new_instance = matches[0]
        for child in old_instance.children.all():
            new_instance.children.add(self._replace_nodes(child, data_nodes))
        return new_instance


class ExpandedDataNodeSerializer(DataNodeSerializer):

    EXPAND = True
