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
            name='Channel',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('channel_name', models.CharField(max_length=255)),
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
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='FileContents',
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
            name='FileImport',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='FileStorageLocation',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('url', models.CharField(max_length=1000)),
                ('status', models.CharField(default=b'incomplete', max_length=256, choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')])),
                ('file_contents', models.ForeignKey(related_name='file_storage_locations', to='analysis.FileContents', null=True)),
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
                ('channel_name', models.CharField(max_length=255)),
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
                ('cores', models.IntegerField()),
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
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='RunRequestInput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(max_length=255)),
                ('channel', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='StepFixedInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('id', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File')])),
                ('channel', models.CharField(max_length=255)),
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
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File')])),
                ('filename', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='StepRuntimeInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('hint', models.CharField(max_length=255, null=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File')])),
                ('channel', models.CharField(max_length=255)),
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
                ('path', models.CharField(max_length=255)),
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
            name='TaskRunInput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('task_definition_input', models.ForeignKey(to='analysis.TaskDefinitionInput')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='TaskRunLocation',
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
            name='TaskRunLog',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('logname', models.CharField(max_length=255)),
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
            name='WorkflowFixedInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('id', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File')])),
                ('channel', models.CharField(max_length=255)),
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
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='WorkflowRuntimeInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('hint', models.CharField(max_length=255, null=True)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File')])),
                ('channel', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('filename', models.CharField(max_length=255)),
                ('metadata', jsonfield.fields.JSONField()),
                ('file_contents', models.ForeignKey(to='analysis.FileContents')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
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
            name='Step',
            fields=[
                ('abstractworkflow_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflow')),
                ('command', models.CharField(max_length=255)),
                ('environment', models.ForeignKey(to='analysis.RequestedEnvironment')),
                ('fixed_inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepFixedInput')),
                ('inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepRuntimeInput')),
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
                ('inputs', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='step_as_input', to='analysis.InputOutputNode')),
                ('outputs', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='step_as_output', to='analysis.InputOutputNode')),
                ('template_step', models.ForeignKey(to='analysis.Step')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflowrun',),
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
            name='Workflow',
            fields=[
                ('abstractworkflow_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflow')),
                ('fixed_inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.WorkflowFixedInput')),
                ('inputs', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.WorkflowRuntimeInput')),
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
                ('inputs', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow_run_as_input', to='analysis.InputOutputNode')),
                ('outputs', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow_run_as_output', to='analysis.InputOutputNode')),
                ('step_runs', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='parent_run', to='analysis.AbstractWorkflowRun')),
                ('template_workflow', models.ForeignKey(to='analysis.Workflow')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflowrun',),
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
            model_name='taskrun',
            name='logs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='task_run', to='analysis.TaskRunLog'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='task_definition',
            field=models.ForeignKey(related_name='task_runs', to='analysis.TaskDefinition'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='task_run_inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='task_run', to='analysis.TaskRunInput'),
        ),
        migrations.AddField(
            model_name='taskrun',
            name='task_run_outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='task_run', to='analysis.TaskRunOutput'),
        ),
        migrations.AddField(
            model_name='taskdefinitioninput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject'),
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
            name='inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.RunRequestInput'),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='workflow',
            field=models.ForeignKey(to='analysis.AbstractWorkflow'),
        ),
        migrations.AddField(
            model_name='fileimport',
            name='file_storage_location',
            field=models.ForeignKey(to='analysis.FileStorageLocation', null=True),
        ),
        migrations.AddField(
            model_name='channeloutput',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='channeloutput',
            name='receiver',
            field=models.ForeignKey(related_name='from_channel', to='analysis.InputOutputNode'),
        ),
        migrations.AddField(
            model_name='channel',
            name='channel_outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.ChannelOutput'),
        ),
        migrations.AddField(
            model_name='channel',
            name='sender',
            field=models.ForeignKey(related_name='to_channel', to='analysis.InputOutputNode'),
        ),
        migrations.AddField(
            model_name='taskrunlog',
            name='logfile',
            field=models.ForeignKey(to='analysis.FileDataObject'),
        ),
        migrations.AddField(
            model_name='fileimport',
            name='file_data_object',
            field=models.ForeignKey(related_name='file_import', to='analysis.FileDataObject'),
        ),
    ]
