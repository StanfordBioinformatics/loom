class InputSet:
    """Represents the set of inputs needed for running one analysis step (one StepRun)"""

    def __init__(self, step):
        self.step = step
        self.inputs = {}

    def add_input(self, destination_port_name, source):
        # Source is a DataObject or an output port
        self.inputs[destination_port_name] = source

    def is_data_ready(self):
        return all([source.is_available() for source in self.inputs.values()])

    def get_data_object(self, destination_port_name):
        return self.inputs[destination_port_name].get_data_object()


class AbstractInputSetManager:
    """An InputSetManager creates InputSets, each of which contains the inputs
    for a single StepRun. There are various types to handle branching, gathering,
    and simple non-branching nodes in the workflow.
    """

    def __init__(self, step):
        self.step = step


class SimpleInputSetManager(AbstractInputSetManager):
    """SimpleInputSetManager handles only simple cases where no loops are 
    beginning or ending. (A loop may be in progress, however, if it started 
    prior to the current step and will close later)
    """

    def are_step_runs_pending(self):
        # TODO. Will fail for parallel
        return not self.step.step_runs.exists()

    def get_available_input_sets(self):
        """For each Port on current Step (here only one)
        Get sources (either DataObject or StepRunOutputPort)
        For Each source, return a set of data needed to create a StepRun
        """

        # TODO handle multiple StepRuns
        input_set = InputSet(self.step)
        for step_input_port in self.step.input_ports.all():
            connector = step_input_port.get_connector()
            if connector.is_data_pipe():
                source_step = connector.get_source_step()
                source_step_run = source_step.step_runs.first()
                source_step_run_output_port = source_step_run.get_output_port(connector.source.port)
                input_set.add_input(step_input_port.name, source_step_run_output_port)
            else:
                input_set.add_input(step_input_port.name, connector.get_data_object())
        return [input_set]


    class ForLoopBeginInputSetManager(AbstractInputSetManager):
        pass


    class ForLoopEndInputSetManager(AbstractInputSetManager):
        pass


class InputSetManagerFactory:
    """Selects the correct InputSetManager for the current step."""

    @classmethod
    def get_input_set_manager(cls, step):
        port_type_count = cls._count_port_types(step)
        if cls._is_for_loop_starting(port_type_count):
            return ForLoopBeginInputSetManager(step)
        elif cls._is_for_loop_ending(port_type_count):
            return ForLoopEndFromArrayInputSetManager(step)
        elif cls._is_no_loop_start_or_end(port_type_count):
            return SimpleInputSetManager(step)
        else:
            raise Exception('invalid configuration')

    @classmethod
    def _count_port_types(cls, step):
        count = {
            'scalar2scalar': 0,
            'array2array': 0,
            'array2scalar': 0,
            'scalar2array': 0
        }
        for port in step.input_ports.all():
            connector = port.get_connector()
            if connector is None:
                # Skip counting if there is no connector. For use in tests only.
                continue
            source_is_array = connector.is_source_an_array()
            destination_is_array = connector.is_destination_an_array()
            if (source_is_array, destination_is_array) == (False, False):
                count['scalar2scalar'] += 1
            elif (source_is_array, destination_is_array) == (True, True):
                count['array2array'] += 1
            elif (source_is_array, destination_is_array) == (True, False):
                count['array2scalar'] += 1
            elif (source_is_array, destination_is_array) == (False, True):
                count['scalar2array'] += 1
            else:
                raise Exception("Port is invalid % port")
        return count

    @classmethod
    def _is_for_loop_starting(cls, port_type_count):
        """Designated by an array output connected to a non-array input port on the current step"""

        if port_type_count['array2scalar'] == 1 and port_type_count['scalar2array'] == 0:
            return True

    @classmethod
    def _is_for_loop_ending(cls, port_type_count):
        """Designated by a non-array output connected to an array input port on the current step"""
        if port_type_count['scalar2array'] == 1 and port_type_count['array2scalar'] == 0:
            return True

    @classmethod
    def _is_no_loop_start_or_end(cls, port_type_count):
        if port_type_count['scalar2array'] == 0 and port_type_count['array2scalar'] == 0:
            return True
