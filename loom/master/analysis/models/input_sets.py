from .files import FileArray


class NoInputs(Exception):
    pass

class NoFilesForSourceArray(Exception):
    pass

class SourceArray(object):
    """Stores a list of StepRunOutputPorts as sources, and is used to
    assemble results from these into a FileArray for input to a
    StepRunInputPort.
    """
    def __init__(self, source_list):
        self.source_list = source_list
        if self._length == 0:
            raise NoFilesForSourceArray()

    def is_available(self):
        return all([source.is_available() for source in self.source_list])

    def get_data_object(self):
        if self._length == 0:
            raise NoFilesForSourceArray()
        if not self.is_available():
            raise Exception("Inputs not ready")
        return FileArray.create(self._render_file_array())

    def _render_file_array(self):
        return {'files': [
                source.get_data_object().to_serializable_obj() 
                for source in self.source_list
                ]}

    def _length(self):
        return len(self.source_list)


class InputSet(object):
    """Represents the set of inputs needed for running one analysis step 
    (one StepRun)
    """

    def __init__(self, ready=True):
        self.inputs = {}
        self.ready = ready

    def add_input(self, destination_port_name, source):
        if self.inputs.get(destination_port_name) is not None:
            raise Exception("Input already exists for port %s" %
                            destination_port_name)
        # Source is a DataObject, StepRunOutputPort, or SourceArray
        self.inputs[destination_port_name] = source

    def is_data_ready(self):
        if self.ready == False:
            return False
        else:
            return all([source.is_available() for source in self.inputs.values()])

    def get_data_object(self, destination_port_name):
        return self.inputs[destination_port_name].get_data_object()


class AbstractInputSetManager(object):
    """An InputSetManager creates InputSets, each of which contains the inputs
    for a single StepRun. There are various types to handle branching, 
    gathering, and simple non-branching nodes in the workflow.
    """

    def __init__(self, step, skip_init_for_testing=False):
        if not skip_init_for_testing:
            self.step = step
            self.input_ports = step.input_ports.all()

    def are_previous_steps_pending(self):
        """True if any previous steps have incomplete StepRuns
        or unassigned InputSets
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
        """Available means the InputSet can be formed, not that associated
        DataObjects are available. As long as the preceding StepRun exists, 
        even if incomplete, an InputSet can be created that contains one or 
        more of its StepRunOutputPorts
        """

        raise Exception("This method should be overridden by a child class")

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
        if len(step_run_output_ports) == 0:
            raise NoInputs()
        assert len(step_run_output_ports) == 1, \
            "Expected nonparallel, but found multiple step runs on source"
        input_set.add_input(step_input_port.name, 
                            step_run_output_ports[0])


class InputlessInputSetManager(AbstractInputSetManager):
    """This InputSetManager is for steps that have no input ports."""

    def __init__(self, step):
        pass

    def are_previous_steps_pending(self):
        # Override
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
        super(SimpleInputSetManager, self).__init__(
            step,
            skip_init_for_testing=skip_init_for_testing)
        if not skip_init_for_testing:
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

    def get_available_input_sets(self):
        """If there are parallel runs on a preceding step, this
        returns a list with one input_set for each run. If there are 
        no parallel runs, it returns a list with single InputSet.
        """
        if len(self.parallel_input_ports) == 0:
            return self._get_available_input_sets_nonparallel()
        else:
            return self._get_available_input_sets_parallel()

    def _get_available_input_sets_nonparallel(self):
        input_set = InputSet()
        try:
            self._add_nonparallel_inputs_to_set(input_set)
        except NoInputs:
            return []
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

    def _get_available_input_sets_parallel(self):
        input_sets = []
        # One InputSet is made for each StepRun on the previous Step.
        for step_run in self._get_step_runs_for_parallel_input_ports():
            input_set = InputSet()
            for step_input_port in self.parallel_input_ports:
                self._add_parallel_input_to_set(
                    input_set, step_input_port, step_run)
            try:
                self._add_nonparallel_inputs_to_set(input_set)
            except NoInputs:
                continue
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


class LoopBeginInputSetManager(AbstractInputSetManager):

    def __init__(self, step, skip_init_for_testing=False):
        super(LoopBeginInputSetManager, self).__init__(
            step,
            skip_init_for_testing=skip_init_for_testing)
        if not skip_init_for_testing:
            self._classify_branching_ports()

    def _classify_branching_ports(self):
        """Find which StepInputPorts have branching input.
        scalar StepInputPorts connected to array DataObjects
        or array StepOutputPorts are classified as
        branching_input_ports. StepInputPorts that are
        array to array or scalar to scalar are classified
        as nonbranching_input_ports.
        """
        self.branching_input_port = None
        self.nonbranching_input_ports = []
        for port in self.input_ports:
            if self._is_branching(port):
                self._add_branching_input_port(port)
            else:
                self._add_nonbranching_input_port(port)

    def _add_branching_input_port(self, port):
        self._validate_branching_input_port(port)
        self.branching_input_port = port

    def _validate_branching_input_port(self, port):
        """One branching port is always allowed.
        More than one are allowed only if they come from the same Step.
        """
        if self.branching_input_port is not None:
            raise Exception("Only one port can be array-to-scalar (begin for"
                            " loop). Multiple array-to-scalar branching ports"
                            " were found: %s and %s" % 
                            (self.branching_input_port.name, 
                             port.name))

    def _add_nonbranching_input_port(self, port):
        """Add without validation. Zero or more nonbranching ports always 
        allowed.
        """
        self.nonbranching_input_ports.append(port)

    def get_available_input_sets(self):
        """There is one port with an array input that will be
        branching to create separate StepRuns. This method returns one 
        InputSet for for each member of that array.
        """
        input_sets = []
        for source  in self._get_branch_sources():
            input_set = InputSet()
            try:
                self._add_branching_input_to_set(
                    input_set, self.branching_input_port, source)
                self._add_nonbranching_inputs_to_set(input_set)
            except NoInputs:
                continue
            input_sets.append(input_set)
        return input_sets

    def _get_branch_sources(self):
        source_array = self.branching_input_port.get_source()
        if source_array is None:
            return []
        elif source_array.is_data_object():
            return source_array.render_as_list()
        else:
            step_run_ports = source_array.get_step_run_ports()
            if len(step_run_ports) > 1:
                raise Exception("Can't branch from an input with"
                                " parallel runs. Branching failed"
                                " on step %s, port %s" % 
                                (self.branching_input_port.name,
                                 self.branching_input_port.step.name,
                                 ))
            if not step_run_ports[0].is_available():
                return []
            else:
                data_object_array = step_run_ports[0].get_data_object()
                return data_object_array.render_as_list()

    def _add_nonbranching_inputs_to_set(self, input_set):
        for step_input_port in self.nonbranching_input_ports:
            self._add_nonbranching_input_to_set(input_set, step_input_port)

    def _add_nonbranching_input_to_set(self, input_set, step_input_port):
        if step_input_port.has_data_binding():
            self._add_input_set_with_data_object_as_source_to_set(
                input_set, step_input_port)
        else:
            self._add_input_set_with_port_as_source_to_set(
                input_set, step_input_port)

    def _add_branching_input_to_set(self, input_set, step_input_port, source):
        input_set.add_input(step_input_port.name, 
                            source)

    def _is_branching(self, port):
        connector = port.get_connector()
        return connector.is_source_an_array()\
                and not connector.is_destination_an_array()

class LoopEndInputSetManager(AbstractInputSetManager):

    def __init__(self, step, skip_init_for_testing=False):
        super(LoopEndInputSetManager, self).__init__(
            step,
            skip_init_for_testing=skip_init_for_testing)
        if not skip_init_for_testing:
            self._classify_merging_ports()

    def _classify_merging_ports(self):
        """Find which StepInputPorts have merging inputs,
        array StepInputPorts connected to scalar DataObjects
        or scalar StepOutputPorts are classified as
        merging_input_ports. StepInputPorts that are
        array to array or scalar to scalar are classified
        as nonbranching_input_ports.
        """
        self.merging_input_ports = []
        self.nonmerging_input_ports = []
        for port in self.input_ports:
            if self._is_merging(port):
                self._add_merging_input_port(port)
            else:
                self._add_nonmerging_input_port(port)

    def _add_merging_input_port(self, port):
        self._validate_merging_input_port(port)
        self.merging_input_ports.append(port)

    def _validate_merging_input_port(self, port):
        """One merging port is always allowed.
        More than one are allowed only if they come from the same Step.
        """
        if len(self.merging_input_ports) > 0 and \
                not port.is_from_same_source_step(
            self.merging_input_ports[0]):
            raise Exception("Only one port can have parallel runs if the ports"
                            " do not connect to the same source step. Parallel"
                            " runs were found on ports %s and %s" % 
                            (self.merging_input_ports[0].name, 
                             port.name))

    def _add_nonmerging_input_port(self, port):
        """Add without validation. Zero or more nonbranching ports always 
        allowed.
        """
        self.nonmerging_input_ports.append(port)

    def get_available_input_sets(self):
        if self.are_previous_steps_pending():
            return [self._get_blocker_input_set()]
        input_set = InputSet()
        try:
            self._add_merging_inputs_to_set(input_set)
            self._add_nonmerging_inputs_to_set(input_set)
        except NoInputs:
            return []
        return [input_set]

    def _get_blocker_input_set(self):
        return InputSet(ready=False)

    def _add_merging_inputs_to_set(self, input_set):
        for input_port in self.merging_input_ports:
            self._add_merging_input_to_set(input_set, input_port)

    def _add_merging_input_to_set(self, input_set, input_port):
        sources_list = input_port.get_source().get_step_run_ports()
        source = SourceArray(sources_list)
        input_set.add_input(input_port.name, source)

    def _get_step_run_output_ports_by_destination(self, input_port):
        return input_port.get_source.get_step_run_output_ports()

    def _add_nonmerging_inputs_to_set(self, input_set):
        for step_input_port in self.nonmerging_input_ports:
            self._add_nonmerging_input_to_set(input_set, step_input_port)

    def _add_nonmerging_input_to_set(self, input_set, step_input_port):
        if step_input_port.has_data_binding():
            self._add_input_set_with_data_object_as_source_to_set(
                input_set, step_input_port)
        else:
            self._add_input_set_with_port_as_source_to_set(
                input_set, step_input_port)

    def _is_merging(self, port):
        connector = port.get_connector()
        return connector.is_destination_an_array()\
                and not connector.is_source_an_array()


class InputSetManagerFactory:
    """Selects the correct InputSetManager for the current step."""

    @classmethod
    def get_input_set_manager(cls, step):
        port_type_count = cls._count_port_types(step)
        if cls._is_for_loop_starting(port_type_count):
            return LoopBeginInputSetManager(step)
        elif cls._is_for_loop_ending(port_type_count):
            return LoopEndInputSetManager(step)
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
