# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import sortedone2many.fields
import universalmodels.models
import django.utils.timezone
import analysis.models.base
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractFileImport',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='AbstractWorkflow',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='AbstractWorkflowRun',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='CancelRequest',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_hard_stop', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=255)),
                ('is_closed_to_new_data', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='ChannelOutput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='DataObjectContent',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='FailureNotice',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_hard_stop', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='FileLocation',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('url', models.CharField(max_length=1000)),
                ('status', models.CharField(default=b'incomplete', max_length=256, choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='FixedStepInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
                ('channel', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='FixedWorkflowInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
                ('channel', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='InputOutputNode',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='RequestedEnvironment',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='RequestedResourceSet',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('memory', models.CharField(max_length=255)),
                ('disk_space', models.CharField(max_length=255)),
                ('cores', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='RestartRequest',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='RunRequest',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_running', models.BooleanField(default=True)),
                ('is_stopping', models.BooleanField(default=False)),
                ('is_hard_stop', models.BooleanField(default=False)),
                ('is_failed', models.BooleanField(default=False)),
                ('is_canceled', models.BooleanField(default=False)),
                ('is_completed', models.BooleanField(default=False)),
                ('cancel_requests', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='run_request', to='analysis.CancelRequest')),
                ('failure_notices', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='run_request', to='analysis.FailureNotice')),
                ('restart_requests', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='run_request', to='analysis.RestartRequest')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='StepInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
                ('channel', models.CharField(max_length=255)),
                ('hint', models.CharField(max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='StepOutput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
                ('filename', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinition',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('command', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinitionEnvironment',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinitionInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskDefinitionOutput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('filename', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskRun',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttempt',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptLogFile',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('log_name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptOutput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskRunInput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskRunOutput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='UnnamedFileContent',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('hash_value', models.CharField(max_length=100)),
                ('hash_function', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='WorkflowInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
                ('channel', models.CharField(max_length=255)),
                ('hint', models.CharField(max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='WorkflowOutput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='AbstractStepRunInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.InputOutputNode')),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='BooleanDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('boolean_value', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='BooleanDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('boolean_content', models.ForeignKey(to='analysis.BooleanDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='FileContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('filename', models.CharField(max_length=255)),
                ('unnamed_file_content', models.ForeignKey(to='analysis.UnnamedFileContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('file_content', models.ForeignKey(to='analysis.FileContent', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='FileImport',
            fields=[
                ('abstractfileimport_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractFileImport')),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractfileimport',),
        ),
        migrations.CreateModel(
            name='FixedWorkflowRunInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.InputOutputNode')),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='IntegerDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('integer_value', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='IntegerDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('integer_content', models.ForeignKey(to='analysis.IntegerDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='JSONDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('json_value', jsonfield.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='JSONDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('json_content', models.ForeignKey(to='analysis.JSONDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='LocalTaskRunAttempt',
            fields=[
                ('taskrunattempt_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.TaskRunAttempt')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.taskrunattempt',),
        ),
        migrations.CreateModel(
            name='MockTaskRunAttempt',
            fields=[
                ('taskrunattempt_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.TaskRunAttempt')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.taskrunattempt',),
        ),
        migrations.CreateModel(
            name='RequestedDockerEnvironment',
            fields=[
                ('requestedenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.RequestedEnvironment')),
                ('docker_image', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.requestedenvironment',),
        ),
        migrations.CreateModel(
            name='RunRequestInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.InputOutputNode')),
                ('channel', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='RunRequestOutput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.InputOutputNode')),
                ('channel', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('abstractworkflow_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflow')),
                ('command', models.CharField(max_length=255)),
                ('environment', models.ForeignKey(to='analysis.RequestedEnvironment')),
                ('fixed_inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.FixedStepInput')),
                ('inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepInput')),
                ('outputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepOutput')),
                ('resources', models.ForeignKey(to='analysis.RequestedResourceSet')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflow',),
        ),
        migrations.CreateModel(
            name='StepRun',
            fields=[
                ('abstractworkflowrun_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflowRun')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflowrun',),
        ),
        migrations.CreateModel(
            name='StepRunOutput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.InputOutputNode')),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='StringDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('string_value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='StringDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('string_content', models.ForeignKey(to='analysis.StringDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='TaskDefinitionDockerEnvironment',
            fields=[
                ('taskdefinitionenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.TaskDefinitionEnvironment')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.taskdefinitionenvironment',),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptLogFileImport',
            fields=[
                ('abstractfileimport_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractFileImport')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractfileimport',),
        ),
        migrations.CreateModel(
            name='TaskRunAttemptOutputFileImport',
            fields=[
                ('abstractfileimport_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractFileImport')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractfileimport',),
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('abstractworkflow_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflow')),
                ('fixed_inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.FixedWorkflowInput')),
                ('inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.WorkflowInput')),
                ('outputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.WorkflowOutput')),
                ('steps', sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='parent_workflow', to='analysis.AbstractWorkflow')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflow',),
        ),
        migrations.CreateModel(
            name='WorkflowRun',
            fields=[
                ('abstractworkflowrun_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflowRun')),
                ('fixed_inputs', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow_run', to='analysis.FixedWorkflowRunInput')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflowrun',),
        ),
        migrations.CreateModel(
            name='WorkflowRunInput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.InputOutputNode')),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
                ('data_object', models.ForeignKey(to='analysis.DataObject', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.inputoutputnode',),
        ),
        migrations.CreateModel(
            name='WorkflowRunOutput',
            fields=[
                ('inputoutputnode_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.InputOutputNode')),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'boolean', b'Boolean'), (b'string', b'String'), (b'integer', b'Integer'), (b'json', b'JSON')])),
                ('data_object', models.ForeignKey(to='analysis.DataObject', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.inputoutputnode',),
        ),
        migrations.AddField(
            model_name='taskrunoutput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='taskrunoutput',
            name='task_definition_output',
            field=models.ForeignKey(to='analysis.TaskDefinitionOutput'),
        ),
        migrations.AddField(
            model_name='taskruninput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='taskruninput',
            name='task_definition_input',
            field=models.ForeignKey(to='analysis.TaskDefinitionInput'),
        ),
        migrations.AddField(
            model_name='taskrunattemptoutput',
            name='data_object',
            field=models.OneToOneField(related_name='task_run_attempt_output', null=True, to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='taskrunattemptoutput',
            name='task_run_output',
            field=models.ForeignKey(to='analysis.TaskRunOutput'),
        ),
        migrations.AddField(
            model_name='taskrunattempt',
            name='log_files',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='task_run_attempt', to='analysis.TaskRunAttemptLogFile'),
        ),
        migrations.AddField(
            model_name='taskrunattempt',
            name='outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='task_run_attempt', to='analysis.TaskRunAttemptOutput'),
        ),
        migrations.AddField(
            model_name='taskrunattempt',
            name='task_run',
            field=models.ForeignKey(to='analysis.TaskRun'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='task_run', to='analysis.TaskRunInput'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='task_run', to='analysis.TaskRunOutput'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='resources',
            field=models.ForeignKey(to='analysis.RequestedResourceSet'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='task_definition',
            field=models.ForeignKey(related_name='task_runs', to='analysis.TaskDefinition'),
        ),
        migrations.AddField(
            model_name='taskdefinitioninput',
            name='data_object_content',
            field=models.ForeignKey(to='analysis.DataObjectContent'),
        ),
        migrations.AddField(
            model_name='taskdefinition',
            name='environment',
            field=models.ForeignKey(to='analysis.TaskDefinitionEnvironment'),
        ),
        migrations.AddField(
            model_name='taskdefinition',
            name='inputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.TaskDefinitionInput'),
        ),
        migrations.AddField(
            model_name='taskdefinition',
            name='outputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.TaskDefinitionOutput'),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='run',
            field=models.OneToOneField(null=True, to='analysis.AbstractWorkflowRun'),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='template',
            field=models.ForeignKey(to='analysis.AbstractWorkflow'),
        ),
        migrations.AddField(
            model_name='filelocation',
            name='unnamed_file_content',
            field=models.ForeignKey(related_name='file_locations', to='analysis.UnnamedFileContent', null=True),
        ),
        migrations.AddField(
            model_name='channeloutput',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='channeloutput',
            name='receiver',
            field=models.OneToOneField(related_name='from_channel', null=True, to='analysis.InputOutputNode'),
        ),
        migrations.AddField(
            model_name='channel',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='channel',
            name='outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.ChannelOutput'),
        ),
        migrations.AddField(
            model_name='channel',
            name='sender',
            field=models.OneToOneField(related_name='to_channel', null=True, to='analysis.InputOutputNode'),
        ),
        migrations.AddField(
            model_name='abstractfileimport',
            name='file_location',
            field=models.ForeignKey(related_name='file_imports', to='analysis.FileLocation', null=True),
        ),
        migrations.AddField(
            model_name='abstractfileimport',
            name='temp_file_location',
            field=models.OneToOneField(related_name='temp_file_import', null=True, to='analysis.FileLocation'),
        ),
        migrations.CreateModel(
            name='FixedStepRunInput',
            fields=[
                ('abstractstepruninput_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractStepRunInput')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractstepruninput',),
        ),
        migrations.CreateModel(
            name='StepRunInput',
            fields=[
                ('abstractstepruninput_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractStepRunInput')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractstepruninput',),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow_run', to='analysis.WorkflowRunInput'),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow_run', to='analysis.WorkflowRunOutput'),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='step_runs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='parent_run', to='analysis.AbstractWorkflowRun'),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='template',
            field=models.ForeignKey(to='analysis.Workflow'),
        ),
        migrations.AddField(
            model_name='taskrunattemptlogfile',
            name='file_data_object',
            field=models.OneToOneField(related_name='task_run_attempt_log_file', null=True, to='analysis.FileDataObject'),
        ),
        migrations.AddField(
            model_name='steprunoutput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='steprunoutput',
            name='task_run_outputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='step_run_outputs', to='analysis.TaskRunOutput'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='step_run', to='analysis.StepRunOutput'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='task_runs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='step_runs', to='analysis.TaskRun'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='template',
            field=models.ForeignKey(related_name='step_run', to='analysis.Step'),
        ),
        migrations.AddField(
            model_name='runrequestoutput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='run_request', to='analysis.RunRequestInput'),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='run_request', to='analysis.RunRequestOutput'),
        ),
        migrations.AddField(
            model_name='fixedworkflowruninput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='filedataobject',
            name='file_import',
            field=models.OneToOneField(related_name='data_object', to='analysis.AbstractFileImport'),
        ),
        migrations.AddField(
            model_name='abstractstepruninput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='abstractstepruninput',
            name='task_run_inputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='step_run_inputs', to='analysis.TaskRunInput'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='fixed_inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='step_run', to='analysis.FixedStepRunInput'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='step_run', to='analysis.StepRunInput'),
        ),
    ]
