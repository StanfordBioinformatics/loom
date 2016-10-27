# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import api.models.base
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractWorkflow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['datetime_created'],
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='AbstractWorkflowRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('status', models.CharField(default=b'', max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField(null=True)),
                ('degree', models.IntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataObjectContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FileImport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FileLocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('url', models.CharField(max_length=1000)),
                ('status', models.CharField(default=b'incomplete', max_length=255, choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FixedStepInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
                ('channel', models.CharField(max_length=255)),
                ('mode', models.CharField(default=b'no_gather', max_length=255)),
                ('group', models.IntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FixedWorkflowInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
                ('channel', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='InputOutputNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RequestedEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RequestedResourceSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('memory', models.CharField(max_length=255, null=True)),
                ('disk_size', models.CharField(max_length=255, null=True)),
                ('cores', models.CharField(max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('is_running', models.BooleanField(default=True)),
                ('is_stopping', models.BooleanField(default=False)),
                ('is_hard_stop', models.BooleanField(default=False)),
                ('is_failed', models.BooleanField(default=False)),
                ('is_canceled', models.BooleanField(default=False)),
                ('is_completed', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='StepInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
                ('channel', models.CharField(max_length=255)),
                ('hint', models.CharField(max_length=255, null=True)),
                ('mode', models.CharField(default=b'no_gather', max_length=255)),
                ('group', models.IntegerField(default=0)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_api.stepinput_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='StepOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
                ('mode', models.CharField(default=b'no_scatter', max_length=255)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_api.stepoutput_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='StepOutputSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=1024, null=True)),
                ('stream', models.CharField(max_length=255, null=True)),
                ('step_output', models.OneToOneField(related_name='source', to='api.StepOutput')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('interpreter', models.TextField()),
                ('command', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinitionEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinitionInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinitionOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
                ('task_definition', models.ForeignKey(related_name='outputs', to='api.TaskDefinition')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinitionOutputSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=1024, null=True)),
                ('stream', models.CharField(max_length=255, null=True)),
                ('task_definition_output', models.OneToOneField(related_name='source', to='api.TaskDefinitionOutput')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('container_id', models.CharField(max_length=255, null=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(default=b'Not started', max_length=255)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_api.taskrunattempt_set+', editable=False, to='contenttypes.ContentType', null=True)),
                ('task_run', models.ForeignKey(related_name='task_run_attempts', to='api.TaskRun')),
                ('task_run_as_accepted_attempt', models.OneToOneField(related_name='accepted_task_run_attempt', null=True, to='api.TaskRun')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=255)),
                ('detail', models.TextField(null=True, blank=True)),
                ('task_run_attempt', models.ForeignKey(related_name='errors', to='api.TaskRunAttempt')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptLogFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('log_name', models.CharField(max_length=255)),
                ('task_run_attempt', models.ForeignKey(related_name='log_files', to='api.TaskRunAttempt')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskRunResourceSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('memory', models.CharField(max_length=255, null=True)),
                ('disk_size', models.CharField(max_length=255, null=True)),
                ('cores', models.CharField(max_length=255, null=True)),
                ('task_run', models.OneToOneField(related_name='resources', to='api.TaskRun')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='UnnamedFileContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash_value', models.CharField(max_length=255)),
                ('hash_function', models.CharField(max_length=255)),
            ],
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='WorkflowImport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='WorkflowInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
                ('channel', models.CharField(max_length=255)),
                ('hint', models.CharField(max_length=255, null=True)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_api.workflowinput_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='WorkflowOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer')])),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_api.workflowoutput_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='AbstractStepRunInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.InputOutputNode')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='BooleanContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObjectContent')),
                ('boolean_value', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='BooleanDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('boolean_content', models.OneToOneField(related_name='data_object', on_delete=django.db.models.deletion.PROTECT, to='api.BooleanContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='FileContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObjectContent')),
                ('filename', models.CharField(max_length=255)),
            ],
            bases=('api.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('source_type', models.CharField(default=b'imported', max_length=255, choices=[(b'imported', b'Imported'), (b'result', b'Result'), (b'log', b'Log')])),
                ('file_content', models.ForeignKey(related_name='file_data_object', on_delete=django.db.models.deletion.PROTECT, to='api.FileContent', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='FixedWorkflowRunInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.InputOutputNode')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='IntegerContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObjectContent')),
                ('integer_value', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='IntegerDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('integer_content', models.OneToOneField(related_name='data_object', on_delete=django.db.models.deletion.PROTECT, to='api.IntegerContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='RequestedDockerEnvironment',
            fields=[
                ('requestedenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.RequestedEnvironment')),
                ('docker_image', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.requestedenvironment',),
        ),
        migrations.CreateModel(
            name='RunRequestInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.InputOutputNode')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='RunRequestOutput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.InputOutputNode')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('abstractworkflow_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.AbstractWorkflow')),
                ('command', models.TextField()),
                ('interpreter', models.TextField(default=b'/bin/bash')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.abstractworkflow',),
        ),
        migrations.CreateModel(
            name='StepRun',
            fields=[
                ('abstractworkflowrun_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.AbstractWorkflowRun')),
                ('template', models.ForeignKey(related_name='step_runs', on_delete=django.db.models.deletion.PROTECT, to='api.Step')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.abstractworkflowrun',),
        ),
        migrations.CreateModel(
            name='StepRunOutput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.InputOutputNode')),
                ('step_output', models.ForeignKey(related_name='step_run_outputs', on_delete=django.db.models.deletion.PROTECT, to='api.StepOutput')),
                ('step_run', models.ForeignKey(related_name='outputs', to='api.StepRun')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='StringContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObjectContent')),
                ('string_value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='StringDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('string_content', models.OneToOneField(related_name='data_object', on_delete=django.db.models.deletion.PROTECT, to='api.StringContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='TaskDefinitionDockerEnvironment',
            fields=[
                ('taskdefinitionenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.TaskDefinitionEnvironment')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.taskdefinitionenvironment',),
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('abstractworkflow_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.AbstractWorkflow')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.abstractworkflow',),
        ),
        migrations.CreateModel(
            name='WorkflowRun',
            fields=[
                ('abstractworkflowrun_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.AbstractWorkflowRun')),
                ('template', models.ForeignKey(related_name='runs', on_delete=django.db.models.deletion.PROTECT, to='api.Workflow')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.abstractworkflowrun',),
        ),
        migrations.CreateModel(
            name='WorkflowRunInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.InputOutputNode')),
                ('workflow_input', models.ForeignKey(related_name='workflow_run_inputs', on_delete=django.db.models.deletion.PROTECT, to='api.WorkflowInput')),
                ('workflow_run', models.ForeignKey(related_name='inputs', to='api.WorkflowRun')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='WorkflowRunOutput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.InputOutputNode')),
                ('workflow_output', models.ForeignKey(related_name='workflow_run_outputs', on_delete=django.db.models.deletion.PROTECT, to='api.WorkflowOutput')),
                ('workflow_run', models.ForeignKey(related_name='outputs', to='api.WorkflowRun')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.inputoutputnode',),
        ),
        migrations.AddField(
            model_name='workflowimport',
            name='workflow',
            field=models.OneToOneField(related_name='workflow_import', to='api.AbstractWorkflow'),
        ),
        migrations.AlterUniqueTogether(
            name='unnamedfilecontent',
            unique_together=set([('hash_value', 'hash_function')]),
        ),
        migrations.AddField(
            model_name='taskrunoutput',
            name='data_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='taskrunoutput',
            name='task_run',
            field=models.ForeignKey(related_name='outputs', to='api.TaskRun'),
        ),
        migrations.AddField(
            model_name='taskruninput',
            name='data_object',
            field=models.ForeignKey(to='api.DataObject', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='taskruninput',
            name='task_run',
            field=models.ForeignKey(related_name='inputs', to='api.TaskRun'),
        ),
        migrations.AddField(
            model_name='taskrunattemptoutput',
            name='data_object',
            field=models.OneToOneField(related_name='task_run_attempt_output', null=True, on_delete=django.db.models.deletion.PROTECT, to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskrunattemptoutput',
            name='task_run_attempt',
            field=models.ForeignKey(related_name='outputs', to='api.TaskRunAttempt'),
        ),
        migrations.AddField(
            model_name='taskrunattemptoutput',
            name='task_run_output',
            field=models.ForeignKey(related_name='task_run_attempt_outputs', on_delete=django.db.models.deletion.PROTECT, to='api.TaskRunOutput'),
        ),
        migrations.AddField(
            model_name='taskrunattemptinput',
            name='data_object',
            field=models.ForeignKey(related_name='task_run_attempt_inputs', on_delete=django.db.models.deletion.PROTECT, to='api.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='taskrunattemptinput',
            name='task_run_attempt',
            field=models.ForeignKey(related_name='inputs', to='api.TaskRunAttempt'),
        ),
        migrations.AddField(
            model_name='taskrunattemptinput',
            name='task_run_input',
            field=models.ForeignKey(related_name='task_run_attempt_inputs', on_delete=django.db.models.deletion.PROTECT, to='api.TaskRunInput', null=True),
        ),
        migrations.AddField(
            model_name='taskdefinitionoutput',
            name='task_run_output',
            field=models.OneToOneField(related_name='task_definition_output', to='api.TaskRunOutput'),
        ),
        migrations.AddField(
            model_name='taskdefinitioninput',
            name='data_object_content',
            field=models.ForeignKey(to='api.DataObjectContent', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='taskdefinitioninput',
            name='task_definition',
            field=models.ForeignKey(related_name='inputs', to='api.TaskDefinition'),
        ),
        migrations.AddField(
            model_name='taskdefinitioninput',
            name='task_run_input',
            field=models.OneToOneField(related_name='task_definition_input', to='api.TaskRunInput'),
        ),
        migrations.AddField(
            model_name='taskdefinitionenvironment',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.taskdefinitionenvironment_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='taskdefinitionenvironment',
            name='task_definition',
            field=models.OneToOneField(related_name='environment', to='api.TaskDefinition'),
        ),
        migrations.AddField(
            model_name='taskdefinition',
            name='task_run',
            field=models.OneToOneField(related_name='task_definition', to='api.TaskRun'),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='run',
            field=models.OneToOneField(related_name='run_request', null=True, on_delete=django.db.models.deletion.PROTECT, to='api.AbstractWorkflowRun'),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='template',
            field=models.ForeignKey(to='api.AbstractWorkflow', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='requestedenvironment',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.requestedenvironment_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='inputoutputnode',
            name='data_root',
            field=models.ForeignKey(related_name='input_output_nodes', to='api.DataNode', null=True),
        ),
        migrations.AddField(
            model_name='inputoutputnode',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.inputoutputnode_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='fixedworkflowinput',
            name='data_object',
            field=models.ForeignKey(to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='fixedworkflowinput',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.fixedworkflowinput_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='fixedstepinput',
            name='data_object',
            field=models.ForeignKey(to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='fixedstepinput',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.fixedstepinput_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='filelocation',
            name='unnamed_file_content',
            field=models.ForeignKey(related_name='file_locations', on_delete=django.db.models.deletion.PROTECT, to='api.UnnamedFileContent', null=True),
        ),
        migrations.AddField(
            model_name='dataobjectcontent',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.dataobjectcontent_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='dataobject',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.dataobject_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='datanode',
            name='data_object',
            field=models.ForeignKey(related_name='data_nodes', to='api.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='datanode',
            name='parent',
            field=models.ForeignKey(related_name='children', to='api.DataNode', null=True),
        ),
        migrations.AddField(
            model_name='abstractworkflowrun',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.abstractworkflowrun_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='abstractworkflow',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_api.abstractworkflow_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.CreateModel(
            name='FixedStepRunInput',
            fields=[
                ('abstractstepruninput_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.AbstractStepRunInput')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.abstractstepruninput',),
        ),
        migrations.CreateModel(
            name='StepRunInput',
            fields=[
                ('abstractstepruninput_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.AbstractStepRunInput')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.abstractstepruninput',),
        ),
        migrations.AddField(
            model_name='workflowoutput',
            name='workflow',
            field=models.ForeignKey(related_name='outputs', to='api.Workflow'),
        ),
        migrations.AddField(
            model_name='workflowinput',
            name='workflow',
            field=models.ForeignKey(related_name='inputs', to='api.Workflow'),
        ),
        migrations.AddField(
            model_name='taskrunoutput',
            name='step_run_output',
            field=models.ForeignKey(related_name='task_run_outputs', to='api.StepRunOutput', null=True),
        ),
        migrations.AddField(
            model_name='taskruninput',
            name='step_run_input',
            field=models.ForeignKey(related_name='task_run_inputs', on_delete=django.db.models.deletion.PROTECT, to='api.AbstractStepRunInput', null=True),
        ),
        migrations.AddField(
            model_name='taskrunattemptlogfile',
            name='file_data_object',
            field=models.OneToOneField(related_name='task_run_attempt_log_file', null=True, on_delete=django.db.models.deletion.PROTECT, to='api.FileDataObject'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='step_run',
            field=models.ForeignKey(related_name='task_runs', to='api.StepRun'),
        ),
        migrations.AddField(
            model_name='stepoutput',
            name='step',
            field=models.ForeignKey(related_name='outputs', to='api.Step'),
        ),
        migrations.AddField(
            model_name='stepinput',
            name='step',
            field=models.ForeignKey(related_name='inputs', to='api.Step'),
        ),
        migrations.AddField(
            model_name='runrequestoutput',
            name='run_request',
            field=models.ForeignKey(related_name='outputs', to='api.RunRequest'),
        ),
        migrations.AddField(
            model_name='runrequestinput',
            name='run_request',
            field=models.ForeignKey(related_name='inputs', to='api.RunRequest'),
        ),
        migrations.AddField(
            model_name='requestedresourceset',
            name='step',
            field=models.OneToOneField(related_name='resources', to='api.Step'),
        ),
        migrations.AddField(
            model_name='requestedenvironment',
            name='step',
            field=models.OneToOneField(related_name='environment', to='api.Step'),
        ),
        migrations.AddField(
            model_name='fixedworkflowruninput',
            name='workflow_input',
            field=models.ForeignKey(related_name='workflow_run_inputs', on_delete=django.db.models.deletion.PROTECT, to='api.FixedWorkflowInput'),
        ),
        migrations.AddField(
            model_name='fixedworkflowruninput',
            name='workflow_run',
            field=models.ForeignKey(related_name='fixed_inputs', to='api.WorkflowRun'),
        ),
        migrations.AddField(
            model_name='fixedworkflowinput',
            name='workflow',
            field=models.ForeignKey(related_name='fixed_inputs', to='api.Workflow'),
        ),
        migrations.AddField(
            model_name='fixedstepinput',
            name='step',
            field=models.ForeignKey(related_name='fixed_inputs', to='api.Step'),
        ),
        migrations.AddField(
            model_name='fileimport',
            name='file_data_object',
            field=models.OneToOneField(related_name='file_import', to='api.FileDataObject'),
        ),
        migrations.AddField(
            model_name='filedataobject',
            name='file_location',
            field=models.ForeignKey(related_name='file_data_object', on_delete=django.db.models.deletion.PROTECT, to='api.FileLocation', null=True),
        ),
        migrations.AddField(
            model_name='filecontent',
            name='unnamed_file_content',
            field=models.ForeignKey(related_name='file_contents', on_delete=django.db.models.deletion.PROTECT, to='api.UnnamedFileContent'),
        ),
        migrations.AddField(
            model_name='abstractworkflowrun',
            name='parent',
            field=models.ForeignKey(related_name='step_runs', to='api.WorkflowRun', null=True),
        ),
        migrations.AddField(
            model_name='abstractworkflow',
            name='parent_workflow',
            field=models.ForeignKey(related_name='steps', to='api.Workflow', null=True),
        ),
        migrations.AddField(
            model_name='stepruninput',
            name='step_input',
            field=models.ForeignKey(related_name='step_run_inputs', on_delete=django.db.models.deletion.PROTECT, to='api.StepInput'),
        ),
        migrations.AddField(
            model_name='stepruninput',
            name='step_run',
            field=models.ForeignKey(related_name='inputs', to='api.StepRun'),
        ),
        migrations.AddField(
            model_name='fixedstepruninput',
            name='step_input',
            field=models.ForeignKey(related_name='step_run_inputs', on_delete=django.db.models.deletion.PROTECT, to='api.FixedStepInput'),
        ),
        migrations.AddField(
            model_name='fixedstepruninput',
            name='step_run',
            field=models.ForeignKey(related_name='fixed_inputs', to='api.StepRun'),
        ),
        migrations.AlterUniqueTogether(
            name='filecontent',
            unique_together=set([('filename', 'unnamed_file_content')]),
        ),
    ]
