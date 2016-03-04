# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import sortedone2many.fields
import universalmodels.models
import analysis.models.base
import sortedm2m.fields
import jsonfield.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
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
            name='DataSourceRecord',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('source_description', models.TextField(max_length=10000)),
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
            name='FileStorageLocation',
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
                ('cores', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('step_name', models.CharField(max_length=255)),
                ('command', models.CharField(max_length=255)),
                ('interpreter', models.CharField(max_length=255)),
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
                ('from_channel', models.CharField(max_length=255)),
                ('to_path', models.CharField(max_length=255)),
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
                ('from_path', models.CharField(max_length=255)),
                ('to_channel', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='StepRun',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(default=b'waiting', max_length=255, choices=[(b'waiting', b'Waiting'), (b'running', b'Running'), (b'completed', b'Completed')])),
                ('step', models.ForeignKey(to='analysis.Step')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='StepRunInput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('step_input', models.ForeignKey(to='analysis.StepInput')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='StepRunOutput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('channel', models.ForeignKey(to='analysis.Channel', null=True)),
                ('step_output', models.ForeignKey(to='analysis.StepOutput', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='Subchannel',
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
                ('status', models.CharField(default=b'running', max_length=255, choices=[(b'running', b'Running'), (b'completed', b'Completed')])),
                ('task_definition', models.ForeignKey(related_name='task_runs', to='analysis.TaskDefinition')),
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
            name='Workflow',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('workflow_name', models.CharField(max_length=255)),
                ('steps', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.Step')),
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
                ('to_channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'file_array', b'File Array'), (b'boolean', b'Boolean'), (b'boolean_array', b'Boolean Array'), (b'string', b'String'), (b'string_array', b'String Array'), (b'integer', b'Integer'), (b'integer_array', b'Integer Array'), (b'float', b'Float'), (b'float_array', b'Float Array'), (b'json', b'JSON'), (b'json_array', b'JSON Array')])),
                ('prompt', models.CharField(max_length=255)),
                ('value', jsonfield.fields.JSONField(null=True)),
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
                ('from_channel', models.CharField(max_length=255)),
                ('output_name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='WorkflowRun',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(default=b'running', max_length=255, choices=[(b'running', b'Running'), (b'completed', b'Completed')])),
                ('channels', sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.Channel')),
                ('step_runs', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow_run', to='analysis.StepRun')),
                ('workflow', models.ForeignKey(to='analysis.Workflow')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='WorkflowRunInput',
            fields=[
                ('_id', models.UUIDField(default=universalmodels.models.uuid_str, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('channel', models.ForeignKey(to='analysis.Channel', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelMixin),
        ),
        migrations.CreateModel(
            name='WorkflowRunOutput',
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
            name='BooleanDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('boolean_value', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='DataObjectArray',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('file_name', models.CharField(max_length=255)),
                ('metadata', jsonfield.fields.JSONField()),
                ('file_contents', models.ForeignKey(to='analysis.FileContents')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='GoogleCloudStorageLocation',
            fields=[
                ('filestoragelocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.FileStorageLocation')),
                ('project_id', models.CharField(max_length=256)),
                ('bucket_id', models.CharField(max_length=256)),
                ('blob_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.filestoragelocation',),
        ),
        migrations.CreateModel(
            name='IntegerDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('integer_value', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='JSONDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('json_data', jsonfield.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='RequestedDockerImage',
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
            name='ServerStorageLocation',
            fields=[
                ('filestoragelocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.FileStorageLocation')),
                ('host_url', models.CharField(max_length=256)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.filestoragelocation',),
        ),
        migrations.CreateModel(
            name='StringDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('string_value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='TaskDefinitionDockerImage',
            fields=[
                ('taskdefinitionenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.TaskDefinitionEnvironment')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.taskdefinitionenvironment',),
        ),
        migrations.AddField(
            model_name='workflowrunoutput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='workflowrunoutput',
            name='subchannel',
            field=models.ForeignKey(to='analysis.Subchannel', null=True),
        ),
        migrations.AddField(
            model_name='workflowrunoutput',
            name='workflow_output',
            field=models.ForeignKey(to='analysis.WorkflowOutput'),
        ),
        migrations.AddField(
            model_name='workflowruninput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='workflowruninput',
            name='workflow_input',
            field=models.ForeignKey(to='analysis.WorkflowInput'),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='workflow_run_inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.WorkflowRunInput'),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='workflow_run_outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.WorkflowRunOutput'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='workflow_inputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.WorkflowInput'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='workflow_outputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.WorkflowOutput'),
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
            model_name='subchannel',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='steprunoutput',
            name='task_run_outputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='step_run_outputs', to='analysis.TaskRunOutput'),
        ),
        migrations.AddField(
            model_name='stepruninput',
            name='subchannel',
            field=models.ForeignKey(to='analysis.Subchannel', null=True),
        ),
        migrations.AddField(
            model_name='stepruninput',
            name='task_run_inputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.TaskRunInput'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='step_run_inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.StepRunInput'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='step_run_outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.StepRunOutput'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='task_runs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.TaskRun'),
        ),
        migrations.AddField(
            model_name='step',
            name='environment',
            field=models.ForeignKey(to='analysis.RequestedEnvironment'),
        ),
        migrations.AddField(
            model_name='step',
            name='resources',
            field=models.ForeignKey(to='analysis.RequestedResourceSet'),
        ),
        migrations.AddField(
            model_name='step',
            name='step_inputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepInput'),
        ),
        migrations.AddField(
            model_name='step',
            name='step_outputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepOutput'),
        ),
        migrations.AddField(
            model_name='filestoragelocation',
            name='file_contents',
            field=models.ForeignKey(related_name='file_storage_locations', to='analysis.FileContents', null=True),
        ),
        migrations.AddField(
            model_name='datasourcerecord',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='data_source_records', to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='channel',
            name='subchannels',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.Subchannel'),
        ),
        migrations.AddField(
            model_name='dataobjectarray',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='parent', to='analysis.DataObject'),
        ),
    ]
