import copy
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from .async_safe_mptt import AsyncSafeMPTTModel, TreeForeignKey

from .base import BaseModel
from .data_objects import DataObject
from api.models import uuidstr
from api.models import validators


"""DataNodes allow DataObjects to be organized into trees.

This is useful in two contexts:

1. To define an array of data as input or output to an
analysis step

2. To organize data produced by parallel analysis. By organizing
data into a tree instead of an array, it is possible to nest
parallel workflows to create scatter-scatter-gather-gather patterns.

Trees of DataNodes may be cloned without duplicating the underlying
DataObjects
"""


class IndexOutOfRangeError(Exception):
    pass
class DegreeMismatchError(Exception):
    pass
class UnknownDegreeError(Exception):
    pass
class NodeAlreadyExistsError(Exception):
    pass
class DataAlreadyExistsError(Exception):
    pass
class UnexpectedLeafNodeError(Exception):
    pass
class MissingBranchError(Exception):
    pass
class DataOnNonLeafError(Exception):
    pass
class DegreeMismatchException(Exception):
    pass


class DataNode(AsyncSafeMPTTModel, BaseModel):

    uuid = models.CharField(default=uuidstr,
                            unique=True, max_length=255)
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        db_index=True,
        related_name = 'children',
        on_delete=models.CASCADE)
    # 0 <= index < self.parent.degree; null if no parent
    index = models.IntegerField(null=True, blank=True)
    # degree is expected number of children; null if leaf, 0 if empty branch
    degree = models.IntegerField(null=True, blank=True,
                                 validators=[validators.validate_ge0])
    data_object = models.ForeignKey('DataObject',
                                    related_name = 'data_nodes',
                                    null=True, # null except on leaves
                                    blank=True,
                                    on_delete=models.PROTECT)
    type = models.CharField(
        max_length=255,
        choices=DataObject.DATA_TYPE_CHOICES)

    EMPTY_BRANCH_VALUE = []

    @property
    def contents(self):
        # Dummy placeholder for serializer
        pass

    def add_leaf(self, index, data_object):
        """Adds a new leaf node at the given index with the given data_object
        """
        assert self.type == data_object.type, 'data type mismatch'
        if self._get_child_by_index(index) is not None:
            raise NodeAlreadyExistsError(
                'Leaf data node already exists at this index')
        else:
            data_node = DataNode(
                parent=self,
                index=index,
                data_object=data_object,
                type=self.type)
            data_node.full_clean()
            data_node.save()
            return data_node

    def add_blank(self, index):
        if self._get_child_by_index(index):
            raise NodeAlreadyExistsError()
        data_node = DataNode(
            parent=self,
            index=index,
            type=self.type)
        data_node.full_clean()
        data_node.save()
        return data_node

    def add_branch(self, index, degree):
        existing_branch = self._get_branch_by_index(index, degree)
        if existing_branch is not None:
            return existing_branch
        else:
            data_node = DataNode(
                parent=self,
                index=index,
                degree=degree,
                type=self.type)
            data_node.full_clean()
            data_node.save()
            return data_node

    def add_data_object(self, data_path, data_object):
        # 'data_path' is a list of (index, degree) pairs
        if not data_path:
            # Set the data object on this node
            if self.data_object is not None:
                raise DataAlreadyExistsError(
                    'Failed to add new data to data node %s because '\
                    'data_node is already set' % self.uuid)
            self.setattrs_and_save_with_retries({'data_object': data_object})
        else:
            if self.degree is None:
                self.setattrs_and_save_with_retries({'degree': data_path[0][1]})
            data_path = copy.deepcopy(data_path)
            self._extend_to_data_path(data_path, leaf_data=data_object)

    def get_data_object(self, data_path):
        node = self.get_node(data_path)
        return node._get_value()

    def has_data_object(self, data_path):
        try:
            data_object = self.get_data_object(data_path)
        except MissingBranchError:
            return False
        return bool(data_object)

    def get_ready_data_nodes(self, seed_path, gather_depth):
        """Returns a list [(path1,data_node1),...]
        with entries only for existing nodes with DataObjects where is_ready==True.
        Missing nodes or those with non-ready or non-existing data are ignored.
        """
        try:
            seed_node = self.get_node(seed_path)
        except MissingBranchError:
            return []
        all_paths = seed_node._get_all_paths(seed_path, gather_depth)
        ready_data_nodes = []
        for path in all_paths:
            if self.is_ready(data_path=path):
                ready_data_nodes.append((path, self.get_node(path)))
        return ready_data_nodes

    def _get_all_paths(self, seed_path, gather_depth):
        if self.is_leaf:
            path = copy.copy(seed_path)
            # If depth exceeds height of tree, just gather to the tree height.
            if gather_depth > len(path):
                gather_depth = len(path)
            if gather_depth == 0:
                return [path,]
            else:
                # Truncate the last 'gather_depth' elements in path
                return [path[:-gather_depth],]
        else:
            # Recursively get paths to leaf nodes
            paths = []
            last_paths = None
            for child in self.children.all():
                path = seed_path + [(child.index, self.degree),]
                new_paths = child._get_all_paths(path, gather_depth)
                if not new_paths == last_paths:
                    # Skip duplicates, otherwise add to list
                    paths.extend(new_paths)
                    last_paths = new_paths
            # Convert to set to remove duplicates created by gathering
            return paths
        
    def is_ready(self, data_path=None):
        # True if all data at or below the given index is ready.
        if data_path is not None:
            # Look at the node designated by data_path to see if it is ready
            try:
                node = self.get_node(data_path)
            except MissingBranchError:
                return False
            return node.is_ready()
        else:
            if self.is_leaf:
                # A leaf node is ready if it has data and that data is ready.
                if self.data_object:
                    return self.data_object.is_ready
                else:
                    return  False
            else:
                # A branch node is ready if all its children are ready
                return all([self._is_child_ready_by_index(i)
                            for i in range(self.degree)])

    def _is_child_ready_by_index(self, index):
        # True if child of given index is ready
        child = self._get_child_by_index(index)
        if child:
            return child.is_ready()
        else:
            return False

    def get_node(self, data_path):
        # 'data_path' is a list of (index, degree) pairs
        if not data_path:
            return self
        if self._is_blank_node():
            raise MissingBranchError(
                'Node is incomplete')
        else:
            data_path = copy.deepcopy(data_path)
            (index, degree) = data_path.pop(0)
            if self.degree != degree:
                raise DegreeMismatchError()
            child = self._get_child_by_index(index)
            if child is None:
                raise MissingBranchError(
                    'Requested branch is missing')
            return child.get_node(data_path)

    def get_or_create_node(self, data_path):
        if not data_path:
            return self
        data_path = copy.deepcopy(data_path)
        return self._extend_to_data_path(data_path)

    def _get_child_by_index(self, index):
        self._check_index(index)
        try:
            child = self.children.get(index=index)
        except ObjectDoesNotExist:
            child = None
        return child

    def _get_branch_by_index(self, index, degree):
        branch = self._get_child_by_index(index)
        if branch is not None:
            if branch.is_leaf:
                raise UnexpectedLeafNodeError('Expected branch but found leaf')
            if branch.degree != degree:
                raise DegreeMismatchError(
                    'Degree of branch conflicts with a value set previously')
        return branch

    def _get_value(self):
        if self._is_empty_branch():
            return self.EMPTY_BRANCH_VALUE
        else:
            return self.data_object

    def _is_empty_branch(self):
        return self.degree==0

    def _extend_to_data_path(self, data_path, leaf_data=None):
        # 'data_path' is a list of (index, degree) pairs
        index, degree = data_path.pop(0)
        if self.degree:
            if not self.degree == degree:
                raise DegreeMismatchException()
        else:
            self.setattrs_and_save_with_retries({'degree': degree})
        if len(data_path) == 0:
            if leaf_data:
                return self.add_leaf(index, leaf_data)
            else:
                try:
                    return self.add_blank(index)
                except NodeAlreadyExistsError:
                    return self._get_child_by_index(index)
        child_degree = data_path[0][1]
        child = self.add_branch(index, child_degree)
        return child._extend_to_data_path(data_path, leaf_data=leaf_data)

    def _check_index(self, index):
        """Verify that the given index is consistent with the degree of the node.
        """
        if self.degree is None:
            raise UnknownDegreeError(
                'Cannot access child DataNode on a parent with degree of None. '\
                'Set the degree on the parent first.')
        if index < 0 or index >= self.degree:
            raise IndexOutOfRangeError(
                'Out of range index %s. DataNode parent has degree %s, so index '\
                'should be in the range 0 to %s' % (
                    index, self.degree, self.degree-1))

    @property
    def is_leaf(self):
        return self.degree is None

    def _is_blank_node(self):
        # Could be a leaf missing data, or a branch missing sub-nodes
        return (self.degree is None is self.data_object is None)

    def _render_as_data_object_list(self):
        if self.is_leaf:
            if self.data_object is None:
                raise Exception(
                    'Failed to render as data object array because data is missing')
            return [self.data_object]
        else:
            data_object_list = []
            for child in self.children.order_by('index'):
                data_object_list += child._render_as_data_object_list()
            return data_object_list

    @property
    def substitution_value(self):
        if self.is_leaf:
            return self.data_object.substitution_value
        else:
            return [child.substitution_value for child
                    in self.children.order_by('index')]

    @property
    def downstream_run_inputs(self):
        assert not self.parent, "RunInputs are connected to the root node"
        return self.runinput_set

    def clone(self, parent=None, seed=None):
        assert not (parent and seed)

        if seed is not None:
            clone = seed
            assert clone.type == self.type, 'type mismatch'
            assert clone.degree is None
            assert clone.data_object is None
            # clone.index may be set because the seed
            # might be connected to a parent.
            clone.setattrs_and_save_with_retries({
                'degree': self.degree,
                'data_object': self.data_object})
        else:
            clone = DataNode(
                parent=parent,
                index=self.index,
                degree=self.degree,
                data_object=self.data_object,
                type=self.type)
            clone.full_clean()
            clone.save()

        for child in self.children.all():
            child.clone(parent=clone)

        return clone

    def flattened_clone(self):
        if self.is_leaf:
            return self.clone()

        leaves = self._get_leaves()

        clone = DataNode(
            degree=len(leaves),
            type=self.type)
        clone.full_clean()
        clone.save()

        index_counter = 0
        for leaf in leaves:
            data_node = DataNode(
                parent=clone,
                index=index_counter,
                data_object=leaf.data_object,
                type=leaf.type)
            data_node.full_clean()
            data_node.save()
            index_counter += 1
        return clone

    def _get_leaves(self):
        if self.is_leaf:
            return [self]

        leaves = []
        for child in self.children.all():
            leaves.extend(child._get_leaves())
        return leaves
