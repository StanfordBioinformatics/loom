import copy
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

from .base import BaseModel
from api.models.data_objects import DataObject, ArrayDataObject
from api.models import uuidstr


"""
Data under each InputOutputNode is represented as a tree of DataTreeNodes. This
lets us represent multidimensional data to allow for nested scatter-gather,
e.g. scatter-scatter-gather-gather, where the layers of scatter are maintained
as distinct.
"""


class IndexOutOfRangeError(Exception):
    pass
class DegreeMismatchError(Exception):
    pass
class UnknownDegreeError(Exception):
    pass
class LeafAlreadyExistsError(Exception):
    pass
class DataAlreadyExistsError(Exception):
    pass
class UnexpectedLeafNodeError(Exception):
    pass
class MissingBranchError(Exception):
    pass
class DataOnNonLeafError(Exception):
    pass

def degree_validator(value):
    if value < 0:
        raise ValidationError('degree must be > 0. Invalid value "%s"' % value)

class DataTreeNode(BaseModel):
    uuid = models.CharField(default=uuidstr,
                            unique=True, max_length=255)
    root_node = models.ForeignKey('DataTreeNode',
                                  null=True,
                                  blank=True,
                                  related_name='descendants',
                                  on_delete=models.SET_NULL)
    parent = models.ForeignKey(
        'DataTreeNode',
        null=True,
        blank=True,
        related_name = 'children',
        on_delete=models.PROTECT)
    # 0 <= index < self.parent.degree; null if no parent
    index = models.IntegerField(null=True, blank=True)
    # degree is expected number of children; null if leaf, 0 if empty branch
    degree = models.IntegerField(null=True, blank=True,
                                 validators=[degree_validator])
    data_object = models.ForeignKey('DataObject',
                                    related_name = 'data_tree_nodes',
                                    null=True, # null except on leaves
                                    blank=True)
    type = models.CharField(
        max_length=255,
        choices=DataObject.DATA_TYPE_CHOICES)

    EMPTY_BRANCH_VALUE = []

    @classmethod
    def create_from_scalar(self, data_object):
        data_tree_node = DataTreeNode.objects.create(type=data_object.type)
        data_tree_node.root_node = data_tree_node
        data_tree_node.data_object = data_object
        data_tree_node.index = 0
        data_tree_node.save()
        return data_tree_node

    def add_leaf(self, index, data_object):
        """Adds a new leaf node at the given index with the given data_object
        """
        assert self.type == data_object.type, 'data type mismatch'
        if self._get_child_by_index(index) is not None:
            raise LeafAlreadyExistsError(
                'Leaf data node already exists at this index')
        else:
            return DataTreeNode.objects.create(
                parent=self,
                root_node=self.root_node,
                index=index,
                data_object=data_object,
                type=self.type)

    def add_branch(self, index, degree):
        existing_branch = self._get_branch_by_index(index, degree)
        if existing_branch is not None:
            return existing_branch
        else:
            return DataTreeNode.objects.create(
                parent=self,
                root_node=self.root_node,
                index=index,
                degree=degree,
                type=self.type)

    def add_data_object(self, data_path, data_object):
        # 'data_path' is a list of (index, degree) pairs
        if not data_path:
            # Set the data object on this node
            if self.data_object is not None:
                raise DataAlreadyExistsError(
                    'Failed to add new data to data node %s because '\
                    'data_node is already set' % self.uuid)
            self.data_object = data_object
            self.save()
        else:
            if self.degree is None:
                self.degree = data_path[0][1]
                self.save()
            data_path = copy.deepcopy(data_path)
            self._extend_data_path_and_add_data_at_leaf(data_path, data_object)

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
        """Returns a list [(path1,data_tree_node1),...]
        with entries only for existing nodes with DataObjects where is_ready==True.
        Missing nodes or those with non-ready or non-existing data are ignored.
        """
        seed_node = self.get_node(seed_path)
        all_paths = seed_node._get_all_paths(seed_path, gather_depth)
        ready_data_nodes = []
        for path in all_paths:
            if self.is_ready(data_path=path):
                ready_data_nodes.append((path, self.get_node(path)))
        return ready_data_nodes

    def _get_all_paths(self, seed_path, gather_depth):
        if self.is_leaf():
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
        if data_path:
            # Look at the node designated by data_path to see if it is ready
            try:
                node = self.get_node(data_path)
            except MissingBranchError:
                return False
            return node.is_ready()
        else:
            if self.is_leaf():
                # A leaf node is ready if it has data and that data is ready.
                if self.data_object:
                    return self.data_object.is_ready()
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
        else:
            data_path = copy.deepcopy(data_path)
            (index, degree) = data_path.pop(0)
            assert self.degree == degree, 'degree mismatch'
            child = self._get_child_by_index(index)
            if child is None:
                raise MissingBranchError(
                    'Requested branch is missing')
            return child.get_node(data_path)

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
            if branch.is_leaf():
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

    def _extend_data_path_and_add_data_at_leaf(self, data_path, data_object):
        # 'data_path' is a list of (index, degree) pairs
        index, degree = data_path.pop(0)
        assert self.degree == degree, 'degree mismatch'
        if len(data_path) == 0:
            self.add_leaf(index, data_object)
            return
        child_degree = data_path[0][1]
        child = self.add_branch(index, child_degree)
        child._extend_data_path_and_add_data_at_leaf(data_path, data_object)

    def _check_index(self, index):
        """Verify that the given index is consistent with the degree of the node.
        """
        if self.degree is None:
            raise UnknownDegreeError(
                'Cannot access child DataTreeNode on a parent with degree of None. '\
                'Set the degree on the parent first.')
        if index < 0 or index >= self.degree:
            raise IndexOutOfRangeError(
                'Out of range index %s. DataTreeNode parent has degree %s, so index '\
                'should be in the range 0 to %s' % (
                    index, self.degree, self.degree-1))

    def is_leaf(self):
        return self.degree is None

    def _is_blank_node(self):
        # Could be a leaf missing data, or a branch missing sub-nodes
        return (self.degree is None is self.data_object is None)

    def render_as_array_data_object(self):
        data_object_list = self._render_as_data_object_list()
        do = ArrayDataObject.objects.create(is_array=True, type=self.type)
        do.add_members(data_object_list)
        return do

    def _render_as_data_object_list(self):
        if self.is_leaf():
            if self.data_object is None:
                raise Exception(
                    'Failed to render as data object array because data is missing')
            return [self.data_object]
        else:
            data_object_list = []
            for child in self.children.order_by('index'):
                data_object_list += child._render_as_data_object_list()
            return data_object_list
       
    def push_all(self):
        """Push data from all nodes
        """
        self.push([])

    def push(self, data_path):
        """Push any data at or below given path.
        This instructs step_run_inputs to check if they can use the data.
        """
        assert self.id == self.root_node.id, 'Cannot push from non-root node'
        for input in self.stepruninput_set.all():
            input.push(data_path)
