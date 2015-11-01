class InputSet:
    """Represents the set of inputs needed for running one analysis step 
    (one StepRun)
    """

    def __init__(self):
        self.inputs = {}

    def add_input(self, destination_port_name, source):
        if self.inputs.get(destination_port_name) is not None:
            raise Exception("Input already exists for port %s" %
                            destination_port_name)
        # Source is a DataObject or a StepRunOutputPort
        self.inputs[destination_port_name] = source

    def is_data_ready(self):
        return all([source.is_available() for source in self.inputs.values()])

    def get_data_object(self, destination_port_name):
        return self.inputs[destination_port_name].get_data_object()


class AbstractInputSetManager:
    """An InputSetManager creates InputSets, each of which contains the inputs
    for a single StepRun. There are various types to handle branching, 
    gathering, and simple non-branching nodes in the workflow.
    """

    def __init__(self, step):
        self.step = step

    def are_previous_steps_pending(self):
        """If this method returns True, the output of get_available_input_sets
        is expected to change as preceding steps complete more runs.
        """
        raise Exception("This method should be overridden by a child class")

    def get_available_input_sets(self):
        """Available means the InputSet can be formed, not that associated
        DataObjects are available. As long as the preceding StepRun exists, 
        even if incomplete, an InputSet can be created that contains one or 
        more of its StepRunOutputPorts
        """
        raise Exception("This method should be overridden by a child class")


class InputlessInputSetManager(AbstractInputSetManager):
    """This InputSetManager is for steps that have no input ports."""

    def are_previous_steps_pending(self):
        return False

    def get_available_input_sets(self):
        return []


class SimpleInputSetManager(AbstractInputSetManager):
    """This InputSetManager handles steps where no loops are beginning or 
    ending. A loop may be in progress, however, if it started prior to the 
    current step and will close later. In that case one StepInputPort will 
    be receiving from a source with multiple (parallel) StepRuns. There can 
    be more than one parallel StepInputPort only if the source for all 
    parallel ports is a single Step, in which case one StepRun on the 
    current step will be created for each parallel StepRun on that preceding 
    step. If two StepInputPorts were each receiving parallel runs from 
    different steps, we would not have enough information to collate those 
    inputs, since the Step.stepruns relationship is not ordered.
    """

    def __init__(self, step, skip_init_for_testing=False):
        if not skip_init_for_testing:
            self.step = step
            self.input_ports = step.input_ports.all()
            self._classify_parallel_ports()

    def _classify_parallel_ports(self):
        """Find which if any StepInputPorts have parallel input.
        StepInputPorts with a source Step with multiple StepRuns are
        classified as parallel_run_input_ports. 
        StepInputPorts receiving data from Steps with a single StepRun, 
        or with a bound DataObject, are classified as nonparallel_input_ports.
        """
        self.parallel_input_ports = []
        self.nonparallel_input_ports = []
        for port in self.input_ports:
            if port.has_parallel_inputs():
                self._add_parallel_input_port(port)
            else:
                self._add_nonparallel_input_port(port)

    def _add_parallel_input_port(self, port):
        self._validate_parallel_input_port(port)
        self.parallel_input_ports.append(port)

    def _validate_parallel_input_port(self, port):
        """Zero or one parallel ports are  always allowed.
        More than one are allowed only if they come from the same Step.
        """
        if len(self.parallel_input_ports) > 0 and \
                not port.is_from_same_source_step(
            self.parallel_input_ports[0]):
            raise Exception("Only one port can have parallel runs if the ports"
                            " do not connect to the same source step. Parallel"
                            " runs were found on ports %s and %s" % 
                            (self.parallel_input_ports[0].name, 
                             port.name))

    def _add_nonparallel_input_port(self, port):
        """Add without validation. Zero or more nonparallel ports always 
        allowed.
        """
        self.nonparallel_input_ports.append(port)

    def are_previous_steps_pending(self):
        """True if any inputs have StepRuns pending,
        or if any input_sets do not yet have StepRuns.
        """
        return any([step.are_step_runs_pending() for step in 
                self._get_all_source_steps()])

    def _get_all_source_steps(self):
        source_steps = set()
        for port in self.input_ports:
            step = port.get_source_step()
            if step is not None:
                source_steps.add(step)
        return list(source_steps)

    def get_available_input_sets(self):
        """For each Port on current Step (here only one)
        Get sources (either DataObject or StepRunOutputPort)
        For Each source, return a set of data needed to create a StepRun
        """
        if len(self.parallel_input_ports) == 0:
            return self._get_available_input_sets_nonparallel()
        else:
            return self._get_available_input_sets_parallel()

    def _get_available_input_sets_nonparallel(self):
        input_set = InputSet()
        self._add_nonparallel_inputs_to_set(input_set)
        return [input_set]

    def _add_nonparallel_inputs_to_set(self, input_set):
        for step_input_port in self.nonparallel_input_ports:
            self._add_nonparallel_input_to_set(input_set, step_input_port)

    def _add_nonparallel_input_to_set(self, input_set, step_input_port):
        if step_input_port.has_data_binding():
            self._add_input_set_with_data_object_as_source_to_set(
                input_set, step_input_port)
        else:
            self._add_input_set_with_port_as_source_to_set(
                input_set, step_input_port)

    def _add_input_set_with_data_object_as_source_to_set(
        self, input_set, step_input_port):
        input_set.add_input(
            step_input_port.name, 
            step_input_port._get_data_binding().get_data_object())

    def _add_input_set_with_port_as_source_to_set(
        self, input_set, step_input_port):
        step_run_output_ports = step_input_port.get_source(
            ).get_step_run_ports()
        # For use with nonparallel only. Otherwise a StepRun must be selected 
        #   for the source.
        assert len(step_run_output_ports) == 1, \
            "Expected nonparallel, but found multiple step runs on source"
        input_set.add_input(step_input_port.name, 
                            step_run_output_ports[0])

    def _get_available_input_sets_parallel(self):
        input_sets = []
        # One InputSet is made for each StepRun on the previous Step.
        for step_run in self._get_step_runs_for_parallel_input_ports():
            input_set = InputSet()
            for step_input_port in self.parallel_input_ports:
                self._add_parallel_input_to_set(
                    input_set, step_input_port, step_run)
            self._add_nonparallel_inputs_to_set(input_set)
            input_sets.append(input_set)
        return input_sets

    def _add_parallel_input_to_set(self, input_set, step_input_port, step_run):
        source_output_port = step_input_port.get_source()
        input_set.add_input(step_input_port.name, 
                            step_run.get_output_port(source_output_port.name))

    def _get_step_runs_for_parallel_input_ports(self):
        # The source Step should be the same for any parallel_input_port. 
        #   (This is enforced when they are added.) Arbitrarily we select 
        #   it from the first.
        return self.parallel_input_ports[0].get_source_step().step_runs.all()


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
        elif cls._has_no_inputs(port_type_count):
            return InputlessInpuSetManager(step)
        elif cls._is_no_loop_starting_or_ending(port_type_count):
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
                # Skip counting if there is no connector. 
                #   For use in tests only.
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
                raise Exception("Port is invalid" % port)
        return count

    @classmethod
    def _is_for_loop_starting(cls, port_type_count):
        """Designated by an array output connected to a non-array input port
        on the current step
        """
        if port_type_count['array2scalar'] == 1 \
                and port_type_count['scalar2array'] == 0:
            return True
        else:
            return False

    @classmethod
    def _is_for_loop_ending(cls, port_type_count):
        """Designated by a non-array output connected to an array input port 
        on the current step
        """
        if port_type_count['scalar2array'] == 1 \
                and port_type_count['array2scalar'] == 0:
            return True
        else:
            return False

    @classmethod
    def _has_no_inputs(cls, port_type_count):
        if not any(port_type_count):
            return True
        else:
            return False

    @classmethod
    def _is_no_loop_starting_or_ending(cls, port_type_count):
        if port_type_count['scalar2array'] == 0 \
                and port_type_count['array2scalar'] == 0 \
                and not cls._has_no_inputs(port_type_count):
            return True
        else:
            return False
