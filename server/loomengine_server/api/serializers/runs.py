from celery import shared_task
import copy
import jsonschema
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
import django.db
from . import CreateWithParentModelSerializer, RecursiveField, strip_empty_values, \
    match_and_update_by_uuid, reload_models
from api import get_setting
from api.models.runs import Run, UserInput, RunInput, RunOutput, RunEvent
from api.models.tasks import Task, TaskInput, TaskOutput, TaskEvent
from api.models.task_attempts import TaskAttempt, TaskAttemptInput, TaskAttemptOutput, TaskAttemptEvent, TaskAttemptLogFile, TaskMembership
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.templates import TemplateSerializer, URLTemplateSerializer
from api.serializers.tasks import TaskSerializer, URLTaskSerializer
from api.serializers.data_channels import DataChannelSerializer
from api.serializers.data_nodes import DataNodeSerializer
from api.async import async_execute


class UserInputSerializer(DataChannelSerializer):

    # type not required because it is inferred from template
    type = serializers.CharField(required=False)

    class Meta:
        model = UserInput
        fields = ('type', 'channel', 'data')


class RunInputSerializer(DataChannelSerializer):

    class Meta:
        model = RunInput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'group')

    mode = serializers.CharField(required=False)
    group = serializers.IntegerField(required=False)
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunInputSerializer, self).to_representation(instance))


class RunOutputSerializer(DataChannelSerializer):

    class Meta:
        model = RunOutput
        fields = ('type', 'channel', 'as_channel', 'data',
                  'mode', 'source', 'parser')

    mode = serializers.CharField(required=False)
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunOutputSerializer, self).to_representation(instance))


class RunEventSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RunEvent
        fields = ('event', 'detail', 'timestamp', 'is_error')


class RunSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Run
	fields = [
            'uuid',
            'url',
            'name',
            'status',
            'datetime_created',
            'datetime_finished',
            'template',
            'postprocessing_status',
            'status_is_finished',
            'status_is_failed',
            'status_is_killed',
            'status_is_running',
            'status_is_waiting',
            'is_leaf',
            'command',
            'interpreter',
            'environment',
            'resources',
            'notification_addresses',
            'notification_context',
            'user_inputs',
            'inputs',
            'outputs',
            'events',
            'steps',
            'tasks',
            'force_rerun',
            'timeout_hours',
        ]

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(
        required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(
        required=False, format='iso-8601')
    template = URLTemplateSerializer(required=False)
    postprocessing_status = serializers.CharField(required=False)
    status = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_waiting = serializers.BooleanField(required=False)
    is_leaf = serializers.BooleanField(required=False)
    command = serializers.CharField(required=False,
                                    allow_null=True, allow_blank=True)
    interpreter = serializers.CharField(required=False,
                                        allow_null=True, allow_blank=True)
    environment = serializers.JSONField(required=False, allow_null=True)
    resources = serializers.JSONField(required=False, allow_null=True)
    notification_addresses = serializers.JSONField(
        required=False, allow_null=True)
    notification_context = serializers.JSONField(
        required=False, allow_null=True)
    user_inputs = UserInputSerializer(many=True, required=False)
    inputs = RunInputSerializer(many=True, required=False)
    outputs = RunOutputSerializer(many=True, required=False)
    events = RunEventSerializer(many=True, required=False)
    steps = RecursiveField(many=True, required=False)
    tasks = TaskSerializer(many=True, required=False)
    timeout_hours = serializers.FloatField(required=False, write_only=False)
    force_rerun = serializers.BooleanField(required=False, write_only=True)

    def to_representation(self, instance):
        instance.prefetch()
        return strip_empty_values(
            super(RunSerializer, self).to_representation(instance))

    def validate(self, data):
        # Use initial data to include nested models data
        run_data = copy.deepcopy(self.initial_data)
        self._validate_run_data_fields(run_data)

        # In validate(), all unsaved models are created and
        # stored in self._unsaved_* arrays or dicts.
        # In create(), these models will be bulk_saved.
        self._preexisting_runs = []
        self._unsaved_runs = []
        self._unsaved_run_outputs = []
        self._unsaved_run_inputs = []
        self._unsaved_run_user_inputs = []
        self._unsaved_run_events = []
        self._run_parent_relationships = []
        self._task_to_task_attempt_relationships = []
        self._task_to_all_task_attempts_m2m_relationships = []
        # No preexisting tasks expected. Should be deleted with run.
        self._unsaved_tasks = []
        self._unsaved_task_inputs = []
        self._unsaved_task_outputs = []
        self._unsaved_task_events = []
        self._preexisting_task_attempts = [] # May be shared with other runs \
                                          # or remnants of a deleted run that \
                                          # were not yet cleaned up
        self._unsaved_task_attempts = {} # Use dict keys to avoid duplicates
        self._unsaved_task_attempt_inputs = []
        self._unsaved_task_attempt_outputs = []
        self._unsaved_log_files = []
        self._unsaved_task_attempt_events = []

        # UUIDs should be ignored if the run is not in
        # terminal status. Otherwise after completing the run
        # we could have non-matching runs with the same UUID on
        # different Loom servers, and that's bad.
        if not self._has_terminal_status(run_data):
            self._strip_run_and_task_uuids

        if run_data.get('uuid'):
            # First check to see if it matches an
            # existing run.
            try:
                r = Run.objects.get(uuid=data.get('uuid'))
                # If run already exists
                self._root_run_uuid = r.uuid
                self._preexisting_runs.append(r)
                return data
            except Run.DoesNotExist:
                pass

        # Did not find run by UUID. Create a new one.
        root_run = self._create_unsaved_models([run_data,])
        self._root_run_uuid = root_run.uuid
        for model in self._unsaved_runs:
            try:
                model.full_clean()
            except django.core.exceptions.ValidationError as e:
                if hasattr(e, 'message_dict'):
                    raise serializers.ValidationError(e.message_dict)
                else:
                    raise serializers.ValidationError(e)
        return data

    def _has_terminal_status(self, data):
        return data.get('status', '') in [
            'Finished', 'Failed', 'Killed']

    def _strip_run_and_task_uuids(self, data):
        data.pop('uuid', None)
        data.pop('url', None)
        for step in data.get('steps', []):
            self._strip_run_and_task_uuids(step)
        for task in data.get('tasks', []):
            self._strip_run_and_task_uuids(task)

    def validate_user_inputs(self, value):
        channels = set()
        for item in value:
            if item.get('channel') in channels:
                raise serializers.ValidationError(
                    'Found duplicate of channel "%s"' % item.get('channel'))
            channels.add(item.get('channel'))
        return value

    def _validate_run_data_fields(self, run_data):
        data_keys = run_data.keys()
        serializer_keys = self.fields.keys()
        extra_fields = filter(
            lambda key: key not in serializer_keys, data_keys)
        if extra_fields:
            raise serializers.ValidationError(
                'Unrecognized fields %s' % extra_fields)

    def _create_unsaved_models(
            self,
            runs_data,
            parent_model=None):
        if parent_model:
            parent_force_rerun = parent_model.force_rerun
        else:
            parent_force_rerun = False
        for i in range(len(runs_data)):
            run_data = runs_data[i]
            try:
                run = Run.objects.get(uuid=run_data.get('uuid'))
                self._preexisting_runs.append(run)
            except Run.DoesNotExist:
                run = self._create_unsaved_run(
                    run_data, parent_force_rerun,
                    parent_model=parent_model)
            if parent_model:
                self._run_parent_relationships.append(
                    (run.uuid, parent_model.uuid))
            children = run_data.get('steps', [])
            has_children = bool(children)
            if has_children:
                # recurse
                self._create_unsaved_models(
                    children,
                    parent_model=run)
        return run

    def _create_unsaved_run(self, run_data, parent_force_rerun,
                            parent_model=None):
        self._validate_run_data_fields(run_data)
        run_data.setdefault('force_rerun', parent_force_rerun)
        run_copy = copy.deepcopy(run_data)
        template_data = run_copy.pop('template')
        s = TemplateSerializer(data=template_data)
        s.is_valid(raise_exception=True)
        template = s.save()
        run_copy['template'] = template
        inputs = run_copy.pop('inputs', [])
        user_inputs = run_copy.pop('user_inputs', [])
        outputs = run_copy.pop('outputs', [])
        tasks = run_copy.pop('tasks', [])
        events = run_copy.pop('events', [])
        run_copy.pop('steps', None)
        run_copy.pop('url', None)
        run_copy.pop('status', None)

        # Other fields are generated from the template
        # if not already defined in the Run
        run_copy.setdefault('name', template.name)
        run_copy.setdefault(
            'timeout_hours', self._get_timeout_hours(
                run_copy, template, parent_model=parent_model))
        run_copy.setdefault('is_leaf', template.is_leaf)
        run_copy.setdefault('command', template.command)
        run_copy.setdefault('interpreter', template.interpreter)
        run_copy.setdefault('environment', template.environment)
        run_copy.setdefault('resources', template.resources)

        run = Run(**run_copy)
        self._unsaved_runs.append(run)

        # Inputs and outputs are generated from the template
        # if not already defined in the run
        if not inputs:
            inputs = self._create_run_inputs_from_template(template)
        if not outputs:
            outputs = self._create_run_outputs_from_template(template)
        for task in tasks:
            self._create_unsaved_task(task, run)
        for input_data in inputs:
            # create unsaved inputs
            input_copy = copy.deepcopy(input_data)
            input_copy['run'] = run
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_run_inputs.append(RunInput(**input_copy))
        for user_input in user_inputs:
            # create unsaved user_inputs
            input_copy = copy.deepcopy(user_input)
            input_copy['run'] = run
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_run_user_inputs.append(UserInput(**input_copy))
        for output_data in outputs:
            # create unsaved outputs
            output_copy = copy.deepcopy(output_data)
            output_copy['run'] = run
            data = output_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': output_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                output_copy['data_node'] = s.save()
            self._unsaved_run_outputs.append(RunOutput(**output_copy))
        for event in events:
            event['run'] = run
            self._unsaved_run_events.append(RunEvent(**event))
        return run

    def _get_timeout_hours(self, run_data, template, parent_model=None):
        if run_data.get('timeout_hours') is not None:
            return run_data.get('timeout_hours')
        elif template.timeout_hours:
            return template.timeout_hours
        elif parent_model is not None:
            return parent_model.timeout_hours
        return None

    def _create_run_inputs_from_template(self, template):
        inputs = []
        for template_input in template.inputs.all():
            inputs.append({
                'channel': template_input.channel,
                'as_channel': template_input.as_channel,
                'type': template_input.type,
                'group': template_input.group,
                'mode': template_input.mode,
            })
        return inputs

    def _create_run_outputs_from_template(self, template):
        outputs = []
        for template_output in template.outputs:
            outputs.append({
                'channel': template_output.get('channel'),
                'as_channel': template_output.get('as_channel'),
                'type': template_output.get('type'),
                'source': template_output.get('source'),
                'parser': template_output.get('parser'),
            })
        return outputs

    def _create_unsaved_task(self, task_data, run):
        task_attempts = task_data.pop('all_task_attempts', [])
        active_task_attempt = task_data.pop('task_attempt', None)
        inputs = task_data.pop('inputs', [])
        outputs = task_data.pop('outputs', [])
        events = task_data.pop('events', [])
        task_data.pop('url', None)
        task_data.pop('status', None)
        task_data['run'] = run
        task = Task(**task_data)
        self._unsaved_tasks.append(task)
        for input_data in inputs:
            # create unsaved inputs
            input_copy = copy.deepcopy(input_data)
            input_copy['task'] = task
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_task_inputs.append(TaskInput(**input_copy))
        for output_data in outputs:
            output_copy = copy.deepcopy(output_data)
            output_copy['task'] = task
            data = output_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': output_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                output_copy['data_node'] = s.save()
            self._unsaved_task_outputs.append(TaskOutput(**output_copy))
        for event in events:
            event['task'] = task
            self._unsaved_task_events.append(TaskEvent(**event))
        if active_task_attempt:
            self._task_to_task_attempt_relationships.append(
                (task_data.get('uuid'), active_task_attempt.get('uuid')))
        for task_attempt in task_attempts:
            try:
                preexisting_task_attempt = TaskAttempt.objects.get(
                    uuid=task_attempt.get('uuid'))
                self._preexisting_task_attempts.append(
                    preexisting_task_attempt)
                self._task_to_all_task_attempts_m2m_relationships.append(
                    TaskMembership(
                        parent_task=task,
                        child_task_attempt=preexisting_task_attempt))
            except TaskAttempt.DoesNotExist:
                self._create_unsaved_task_attempt(task_attempt, task)

    def _create_unsaved_task_attempt(self, task_attempt_data, task):
        inputs = task_attempt_data.pop('inputs', [])
        outputs = task_attempt_data.pop('outputs', [])
        events = task_attempt_data.pop('events', [])
        log_files = task_attempt_data.pop('log_files', [])
        task_attempt_data.pop('url', None)
        task_attempt_data.pop('status', None)
        task_attempt = TaskAttempt(**task_attempt_data)
        if task_attempt.uuid in self._unsaved_task_attempts.keys():
            return
        self._unsaved_task_attempts[task_attempt.uuid] = task_attempt
        for input_data in inputs:
            input_copy = copy.deepcopy(input_data)
            input_copy['task_attempt'] = task_attempt
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_task_attempt_inputs.append(
                TaskAttemptInput(**input_copy))
        for output_data in outputs:
            output_copy = copy.deepcopy(output_data)
            output_copy['task_attempt'] = task_attempt
            data = output_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': output_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                output_copy['data_node'] = s.save()
            self._unsaved_task_attempt_outputs.append(
                TaskAttemptOutput(**output_copy))
        for log_file in log_files:
            log_file['task_attempt'] = task_attempt
            data_object = log_file.pop('data_object', None)
            log_file.pop('url')
            if data_object:
                s = DataObjectSerializer(data=data_object)
                s.is_valid(raise_exception=True)
                log_file['data_object'] = s.save()
            log_file = TaskAttemptLogFile(**log_file)
            self._unsaved_log_files.append(log_file)
        for event in events:
            event['task_attempt'] = task_attempt
            self._unsaved_task_attempt_events.append(TaskAttemptEvent(**event))
        self._task_to_all_task_attempts_m2m_relationships.append(
            TaskMembership(parent_task=task, child_task_attempt=task_attempt))

    def create(self, validated_data):
        # In create(), the unsaved models created in validate()
        # will be bulk_saved.
        try:
            bulk_runs = Run.objects.bulk_create(self._unsaved_runs)
            self._new_runs = reload_models(Run, bulk_runs)
            all_runs = [run for run in self._new_runs]
            all_runs.extend(self._preexisting_runs)
            match_and_update_by_uuid(
                self._unsaved_run_inputs, 'run', self._new_runs)
            RunInput.objects.bulk_create(self._unsaved_run_inputs)
            match_and_update_by_uuid(
                self._unsaved_run_outputs, 'run', self._new_runs)
            RunOutput.objects.bulk_create(self._unsaved_run_outputs)
            match_and_update_by_uuid(self._unsaved_run_user_inputs,
                                     'run', self._new_runs)
            UserInput.objects.bulk_create(self._unsaved_run_user_inputs)
            match_and_update_by_uuid(
                self._unsaved_run_events, 'run', self._new_runs)
            RunEvent.objects.bulk_create(self._unsaved_run_events)
            match_and_update_by_uuid(
                self._unsaved_tasks, 'run', self._new_runs)
            bulk_tasks = Task.objects.bulk_create(self._unsaved_tasks)
            self._new_tasks = reload_models(Task, bulk_tasks)
            match_and_update_by_uuid(
                self._unsaved_task_inputs, 'task', self._new_tasks)
            TaskInput.objects.bulk_create(self._unsaved_task_inputs)
            match_and_update_by_uuid(self._unsaved_task_outputs,
                                     'task', self._new_tasks)
            TaskOutput.objects.bulk_create(self._unsaved_task_outputs)
            match_and_update_by_uuid(self._unsaved_task_events,
                                     'task', self._new_tasks)
            TaskEvent.objects.bulk_create(self._unsaved_task_events)
            bulk_attempts = TaskAttempt.objects.bulk_create(
                self._unsaved_task_attempts.values())
            self._new_task_attempts = reload_models(TaskAttempt, bulk_attempts)
            all_task_attempts = [task_attempt for task_attempt
                                 in self._new_task_attempts]
            all_task_attempts.extend(self._preexisting_task_attempts)
            match_and_update_by_uuid(self._unsaved_task_attempt_inputs,
                                     'task_attempt', self._new_task_attempts)
            TaskAttemptInput.objects.bulk_create(
                self._unsaved_task_attempt_inputs)
            match_and_update_by_uuid(self._unsaved_task_attempt_outputs,
                                     'task_attempt',self._new_task_attempts)
            TaskAttemptOutput.objects.bulk_create(
                self._unsaved_task_attempt_outputs)
            match_and_update_by_uuid(self._unsaved_task_attempt_events,
                                     'task_attempt', self._new_task_attempts)
            TaskAttemptEvent.objects.bulk_create(
                self._unsaved_task_attempt_events)
            match_and_update_by_uuid(self._unsaved_log_files,
                                     'task_attempt', self._new_task_attempts)
            TaskAttemptLogFile.objects.bulk_create(self._unsaved_log_files)
            self._connect_tasks_to_active_task_attempts(
                self._new_tasks, all_task_attempts)
            match_and_update_by_uuid(
                self._task_to_all_task_attempts_m2m_relationships,
                'parent_task', self._new_tasks)
            match_and_update_by_uuid(
                self._task_to_all_task_attempts_m2m_relationships,
                'child_task_attempt', all_task_attempts)
            TaskMembership.objects.bulk_create(
                self._task_to_all_task_attempts_m2m_relationships)
            self._connect_runs_to_parents(all_runs)
            root_run = filter(
                lambda r: r.uuid==self._root_run_uuid, all_runs)
            assert len(root_run) == 1, '1 run should match uuid of root'
            run = root_run[0]
            async_execute(_create_fingerprints, run.uuid)

            # TODO start new runs
        
            return run
        except Exception as e:
            self._cleanup()
            raise

    def _connect_runs_to_parents(self, runs):
        params = []
        for run_uuid, parent_uuid in self._run_parent_relationships:
            run = filter(
                lambda r: r.uuid==run_uuid, runs)[0]
            parent = filter(
                lambda r: r.uuid==parent_uuid, runs)[0]
            params.append((run.id, parent.id))
        if params:
            case_statement = ' '.join(
                ['WHEN id=%s THEN %s' % pair for pair in params])
            id_list = ', '.join(['%s' % pair[0] for pair in params])
            sql = 'UPDATE api_run SET parent_id= CASE %s END WHERE id IN (%s)'\
                                                 % (case_statement, id_list)
            with django.db.connection.cursor() as cursor:
                cursor.execute(sql)

    def _connect_tasks_to_active_task_attempts(self, tasks, task_attempts):
        params = []
        for task_uuid, task_attempt_uuid in self._task_to_task_attempt_relationships:
            task = filter(lambda t: t.uuid==task_uuid, tasks)[0]
            task_attempt = filter(
                lambda ta: ta.uuid==task_attempt_uuid, task_attempts)[0]
            params.append((task.id, task_attempt.id))
        if params:
            case_statement = ' '.join(
                ['WHEN id=%s THEN %s' % pair for pair in params])
            id_list = ', '.join(['%s' % pair[0] for pair in params])
            sql = 'UPDATE api_task SET task_attempt_id= CASE %s END WHERE id IN (%s)'\
                                                        % (case_statement, id_list)
            with django.db.connection.cursor() as cursor:
                cursor.execute(sql)

    def _cleanup(self):
        if hasattr(self, '_new_runs'):
            self._new_runs.delete()
        if hasattr(self, '_new_tasks'):
            self._new_tasks.delete()
        if hasattr(self, '_new_task_attempts'):
            self._new_task_attempts.delete()

    """
    def _start_run(self, data):
        try:
            user_inputs = self.initial_data.get('user_inputs', None)
            data.pop('user_inputs', None)
            data.pop('template')
            s = TemplateSerializer(data=self.initial_data.get('template'))
            s.is_valid()
            template = s.save()

            run = Run.create_from_template(
                template,
                name=data.get('name'),
                notification_addresses=data.get('notification_addresses'),
                force_rerun=data.get('force_rerun', False),
                notification_context=self._get_notification_context())

            self._new_runs = run # for cleanup if failure

            if user_inputs is not None:
                for input_data in user_inputs:
                    # The user_input usually won't have data type specified.
                    # We need to know the data type to find or create the
                    # data object from the value given. We get the type from
                    # the corresponding template input.
                    if not input_data.get('channel'):
                        raise serializers.ValidationError(
                            'Missing required "channel" field on input: "%s"'
                            % input_data)
                    try:
                        input = template.get_input(input_data.get('channel'))
                    except ObjectDoesNotExist:
                        raise serializers.ValidationError(
                            'Input channel "%s" does not match any channel '\
                            'on the template.' % input_data.get('channel'))
                    if input_data.get('type') \
                       and input_data.get('type') != input.type:
                        raise serializers.ValidationError(
                            'Type mismatch: Data with type "%s" does not '
                            'match input channel "%s" with type "%s".' % (
                                input_data.get('type'),
                                input_data.get('channel'), type))
                    input_data.update({'type': input.type})
                    s = UserInputSerializer(
                        data=input_data,
                        context={'parent_field': 'run',
                                 'parent_instance': run
                        })
                    s.is_valid(raise_exception=True)
                    i = s.save()
                    if not i.data_node.is_ready():
                        raise serializers.ValidationError(
                            'Data for input "%s" is not ready. (Maybe a file '\
                            'upload failed or is not yet complete?)'
                            % i.channel)
            run.initialize_inputs()
            run.initialize_outputs()
            run.initialize()
            return run
        except django.core.exceptions.ValidationError as e:
            self._cleanup()
            raise serializers.ValidationError(e)
        except Exception as e:
            self._cleanup()
            raise
    """

    def _get_notification_context(self):
        context = {
            'server_name': get_setting('SERVER_NAME')}
        request = self.context.get('request')
        if request:
            context.update({
                'server_url': '%s://%s' % (
                    request.scheme,
		    request.get_host()),
	    })
        return context

        
class URLRunSerializer(RunSerializer):

    # readable fields
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(
        required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(
        required=False, format='iso-8601')
    status = serializers.CharField(read_only=True)
    is_leaf = serializers.BooleanField(required=False)

    # write-only fields
    template = URLTemplateSerializer(required=False, write_only=True)
    postprocessing_status = serializers.CharField(required=False, write_only=True)
    status_is_finished = serializers.BooleanField(required=False, write_only=True)
    status_is_failed = serializers.BooleanField(required=False, write_only=True)
    status_is_killed = serializers.BooleanField(required=False, write_only=True)
    status_is_running = serializers.BooleanField(required=False, write_only=True)
    status_is_waiting = serializers.BooleanField(required=False, write_only=True)
    command = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    notification_addresses = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    notification_context = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    user_inputs = UserInputSerializer(
        many=True, required=False, write_only=True)
    inputs = RunInputSerializer(many=True, required=False, write_only=True)
    outputs = RunOutputSerializer(many=True, required=False, write_only=True)
    events = RunEventSerializer(many=True, required=False, write_only=True)
    steps = RecursiveField(many=True, required=False, write_only=True)
    tasks = TaskSerializer(many=True, required=False, write_only=True)
    timeout_hours = serializers.FloatField(required=False, write_only=True)
    force_rerun = serializers.BooleanField(required=False, write_only=True)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunSerializer, self).to_representation(instance))


# Asynchronous
@shared_task
def _create_fingerprints(run_uuid):
    run = Run.objects.get(uuid=run_uuid)
    for step in run.get_leaves():
        for task in step.tasks.all():
            fingerprint = task.get_fingerprint()
            fingerprint.update_task_attempt_maybe(task.task_attempt)
