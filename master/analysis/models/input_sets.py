

"""
class AbstractInputSetManager:
    def __init__(self, step):
        self.step = step

class ForLoopBeginInputSetManager:
    pass

class ForLoopEndInputSetManager:
    pass

class NoLoopInputSetManager:
    pass

class InputSetManagerFactory:
    @classmethod
    port_type_count = self._count_port_types(step)
    def get_input_set_manager(cls, step):
        if self._is_for_loop_starting(port_type_count):
            return ForLoopBeginInputSetManager(step)
        elif self._is_for_loop_ending(port_type_count):
            return ForLoopEndFromArrayInputSetManager(step)
        elif self._is_no_loop_start_or_end(port_type_count):
            return NoLoopInputSetManager(step)
        else:
            raise Exception('invalid configuration')

    @classmethod
    def _count_port_types(cls, step):
        count = {
            'scalar2scalar': 0
            'array2array': 0,
            'array2scalar': 0,
            'scalar2array': 0,
        }
        for port in step.input_ports:
            source_is_array = port.get_connector().is_source_an_array()
            destination_is_array = port.get_connector().is_destination_an_array()
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
        # One part is array-to-scalar
        # Any other parts are straight pass-through
        if port_type_count['array2scalar'] == 1 and port_type_count['scalar2array'] == 0:
            return True

    @classmethod
    def _is_for_loop_ending(cls, port_type_count):
        if port_type_count['scalar2array'] == 1 and port_type_count['array2scalar'] == 0:
            return True

    @classmethod
    def _is_no_loop_start_or_end(cls, port_type_count):
        if port_type_count['scalar2array'] == 0 and port_type_count['array2scalar'] == 0:
            return True
"""


class InputSet:
    # Handles the set of inputs needed to create one StepDefinition

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

class OversimplifiedInputSetManager:

    # Only handles the case of a single input in each port with no parallel processing

    def __init__(self, step):
        self.step = step

    def are_step_runs_pending(self):
        # TODO. Oversimplified. Will fail for parallel
        return not self.step.step_runs.exists()

    def get_available_input_sets(self):
        # For each Port on current Step (here only one)
        # Get sources (either DataObject or StepRunOutputPort)
        # For Each source, return a set of data needed to create a StepRun

        # Assuming that each port has only 1 input, not an array

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
