import copy
import jsonschema

from rest_framework import serializers

from .base import IdSerializer
from .data_objects import DataObjectSerializer
from api.models.data_trees import *
from api.models.data_objects import DataObject


class DataNodeSerializer(serializers.ModelSerializer):

    MISSING_BRANCH_VALUE = None
    EMPTY_BRANCH_VALUE = []

    # Serializes/deserializers a tree of DataObjects.
    # Input is a string, integer, float, boolean, or dict representation 
    # of a DataObject, or a list of [lists of]^n these representations.
    # Output is a dict or list of [lists of]^n dicts.

    contents = serializers.JSONField()

    class Meta:
        model = DataNode
        fields = ('id', 'contents',)

    def create(self, validated_data):
        type = self.context.get('type')
        if not type:
            raise Exception('data type must be set in serializer context')
        contents = self.initial_data.get('contents')
        if contents is None:
            raise Exception('no data contents. Cannot create DataNode')
        return self._create_data_tree_from_data_objects(
                contents, type)

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            return super(self.__class__, self).to_representation(
                self.initial_data)
        else:
            assert isinstance(instance, DataNode)
            return {'id': instance.id, 
                    'contents': self._data_tree_to_data_struct(instance)}

    def validate_contents(self, value):
        try:
            jsonschema.validate(value, self.data_validation_schema)
        except jsonschema.exceptions.ValidationError:
            raise serializers.ValidationError(
                "Data must be a string, number, boolean, or object, a list "\
                "of these, or nested lists of these." \
                "Invalid data: '%s'" % value)
        try:
            self._validate_uniform_height(value)
        except serializers.ValidationError:
            raise serializers.ValidationError(
                "Data must have uniform height. Invalid data: '%s'" % value)
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
            # Non-uniform height. Invalid data.
            raise serializers.ValidationError('Height is not uniform')

        # Add 1 for the current level
        return minheight + 1

    def _create_data_tree_from_data_objects(self, contents, data_type):
        data_node = DataNode.objects.create()
        data_node.root_node = data_node
        data_node.save()
        self._add_data_objects(data_node, contents, data_type)
        return data_node

    def _add_data_objects(self, data_node, contents, data_type):
        path = []
        self._extend_all_paths_and_add_data_at_leaves(
            data_node, contents, path, data_type)

    def _data_tree_to_data_struct(self, data_node):
        if data_node._is_missing_branch():
            return self.MISSING_BRANCH_VALUE
        elif data_node._is_empty_branch():
            return self.EMPTY_BRANCH_VALUE
        if data_node._is_leaf():
            s = DataObjectSerializer(data_node.data_object)
            return s.data
        else:
            contents = [self.MISSING_BRANCH_VALUE] * data_node.degree
            for child in data_node.children.all():
                contents[child.index] = self._data_tree_to_data_struct(child)
            return contents

    def _extend_all_paths_and_add_data_at_leaves(
            self, data_node, contents, path, data_type):
        # Recursive function that extends 'path' until reaching a leaf node,
        # where data is finally added.
        # 'path' is the partial path to some intermediate
        # node, while 'contents' is the representation of all branches and 
        # leaves beyond that path.
        # For example, given path (0,2) and data [['10','20']['30','40']],
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
                s = DataObjectSerializer(data=contents)
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
            data_node.degree = 0
            data_node.save()
        else:
            for i in range(len(contents)):
                path_i = copy.deepcopy(path)
                path_i.append((i, len(contents)))
                self._extend_all_paths_and_add_data_at_leaves(
                    data_node, contents[i], path_i, data_type)

    data_validation_schema = {
        # schema used to verify that data contains only a X,
        # a list of X, or a list of (lists of)^n X,
        # where X is string, integer, float, boolean, or object.
        # These are the only valid structures for user-provided 
        # data values, e.g. 'file.txt@id',
        # '["file1.txt@id1", "file2.txt@id2"]', or
        # '[["file1.txt@id1", "file2.txt@id2"], ["file3.txt@id3"]]'.
        # A DataObject may be used rather than the primitive type.
        'definitions': {
            'stringschema': {
                'oneOf': [
                    { 'type': [ 'string' ] },
                    { 'type': [ 'object' ],
                      'properties': {
                          'type': {'enum': ['string']}
                      },
                      'required': ['type']},
                    { 'type': ['array'], 
                      'items': {
                          '$ref': '#/definitions/stringschema'}}
                ]
            },
            'integerschema': {
                'oneOf': [
                    { 'type': [ 'integer' ] },
                    { 'type': [ 'object' ],
                      'properties': {
                          'type': {'enum': ['integer']}
                      },
                      'required': ['type']},
                    { 'type': ['array'], 
                      'items': {
                          '$ref': '#/definitions/integerschema'}}
                ]
            },
            'floatschema': {
                'oneOf': [
                    { 'type': [ 'number' ] },
                    { 'type': [ 'object' ],
                      'properties': {
                          'type': {'enum': ['float']}
                      },
                      'required': ['type']},
                    { 'type': ['array'], 
                      'items': {
                          '$ref': '#/definitions/floatschema'}}
                ]
            },
            'booleanschema': {
                'oneOf': [
                    { 'type': [ 'boolean' ] },
                    { 'type': [ 'object' ],
                      'properties': {
                          'type': {'enum': ['boolean']}
                      },
                      'required': ['type']},
                    { 'type': ['array'], 
                      'items': {
                          '$ref': '#/definitions/booleanschema'}}
                ]
            }
        },
        'anyOf': [
            {'$ref': '#/definitions/stringschema'},
            {'$ref': '#/definitions/integerschema'},
            {'$ref': '#/definitions/floatschema'},
            {'$ref': '#/definitions/booleanschema'},
        ]
    }

class DataNodeIdSerializer(IdSerializer, DataNodeSerializer):
    pass
