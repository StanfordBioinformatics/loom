class TaskInputManager(object):
    """Manages the set of nodes acting as inputs for one step.
    Each input node may have more than one DataObject,
    and DataObjects may arrive to the node at different times.
    """
    def __init__(self, input_nodes):
        self.input_nodes = input_nodes

    def get_ready_input_sets(self, channel, data_path):
        """New data is available at the given data_path. See whether 
        any new tasks can be created with this data.
        Here 'data_path' refers to the path in the data tree, represented as
        a list of (index, degree) tuples. to traverse from the root node
        to the designated node. This function searches at or below that 
        node for any data that is ready to be processed.
        """
        for input_node in self.input_nodes:
            if not input_node.is_ready(data_path=data_path):
                # At least one node is missing data at this data_path.
                # No InputSets ready.
                return []

        #groups = set()
        #for input_node in self.input_nodes:
        #    self.groups.add(input_node.group)

        #input_nodes_by_group = {}
        #for group in groups:
        #    input_nodes_by_group[group]=filter(
        #        lambda n: n.group==group, self.input_nodes)

        #for node_group in input_nodes_by_group.values():
        #    for input_node in node_group:
        #        if not input_node.is_ready():
        #            return []

        return [InputSet(self.input_nodes, data_path)]


class InputItem(object):
    """Info needed by the Task to construct one TaskInput
    """

    def __init__(self, input_node, data_path):
        self.data_object = input_node.get_data_object(data_path)
        self.type = self.data_object.type
        self.channel = input_node.channel


class InputSet(object):
    """A TaskInputManager can produce one or more InputSets, where each
    InputSet corresponds to a single Task.
    """

    def __init__(self, input_nodes, data_path):
        self.data_path = data_path
        self.input_items = [InputItem(i, data_path) for i in input_nodes]

    def __iter__(self):
        return self.input_items.__iter__()
