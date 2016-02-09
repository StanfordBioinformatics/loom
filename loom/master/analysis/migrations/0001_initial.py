# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import sortedone2many.fields
import django.utils.timezone
import sortedm2m.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
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
        ),
        migrations.CreateModel(
            name='FileName',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileStorageLocation',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProcessLocation',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataBinding',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataBindingDestinationPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('step', models.CharField(max_length=256)),
                ('port', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataPipe',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataPipeDestinationPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('step', models.CharField(max_length=256)),
                ('port', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataPipeSourcePortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('step', models.CharField(max_length=256)),
                ('port', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestEnvironment',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestInputPort',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=256)),
                ('file_name', models.CharField(max_length=256)),
                ('is_array', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestOutputPort',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=256)),
                ('is_array', models.BooleanField(default=False)),
                ('file_name', models.CharField(max_length=256, null=True)),
                ('glob', models.CharField(max_length=256, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestResourceSet',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('memory', models.CharField(max_length=20)),
                ('cores', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=256)),
                ('command', models.CharField(max_length=256)),
                ('constants', jsonfield.fields.JSONField(null=True)),
                ('are_results_complete', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinition',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('command', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionEnvironment',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionInputPort',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('is_array', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionOutputPort',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('file_name', models.CharField(max_length=256, null=True)),
                ('glob', models.CharField(max_length=256, null=True)),
                ('is_array', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepResult',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRun',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('are_results_complete', models.BooleanField(default=False)),
                ('is_running', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunDataBinding',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunDataBindingDestinationPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('port', models.CharField(max_length=256, null=True)),
                ('step_run', models.ForeignKey(to='analysis.StepRun')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunDataPipe',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunDataPipeDestinationPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('port', models.CharField(max_length=256, null=True)),
                ('step_run', models.ForeignKey(to='analysis.StepRun')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunDataPipeSourcePortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('port', models.CharField(max_length=256, null=True)),
                ('step_run', models.ForeignKey(to='analysis.StepRun')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunInputPort',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=256)),
                ('step_definition_input_port', models.ForeignKey(to='analysis.StepDefinitionInputPort', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunOutputPort',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=256)),
                ('step_definition_output_port', models.ForeignKey(to='analysis.StepDefinitionOutputPort', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=256, null=True)),
                ('constants', jsonfield.fields.JSONField(null=True)),
                ('are_results_complete', models.BooleanField(default=False)),
                ('data_bindings', sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.RequestDataBinding')),
                ('data_pipes', sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.RequestDataPipe')),
                ('steps', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow', to='analysis.Step')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('metadata', jsonfield.fields.JSONField(null=True)),
                ('file_contents', models.ForeignKey(to='analysis.FileContents')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='FileArray',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('files', sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.File')),
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
            name='LocalProcessLocation',
            fields=[
                ('processlocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.ProcessLocation')),
                ('pid', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.processlocation',),
        ),
        migrations.CreateModel(
            name='RequestDockerImage',
            fields=[
                ('requestenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.RequestEnvironment')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.requestenvironment',),
        ),
        migrations.CreateModel(
            name='ServerFileStorageLocation',
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
            name='StepDefinitionDockerImage',
            fields=[
                ('stepdefinitionenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.StepDefinitionEnvironment')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.stepdefinitionenvironment',),
        ),
        migrations.AddField(
            model_name='steprundatapipe',
            name='destination',
            field=models.ForeignKey(to='analysis.StepRunDataPipeDestinationPortIdentifier'),
        ),
        migrations.AddField(
            model_name='steprundatapipe',
            name='source',
            field=models.ForeignKey(to='analysis.StepRunDataPipeSourcePortIdentifier'),
        ),
        migrations.AddField(
            model_name='steprundatabinding',
            name='destination',
            field=models.ForeignKey(to='analysis.StepRunDataBindingDestinationPortIdentifier'),
        ),
        migrations.AddField(
            model_name='steprundatabinding',
            name='source',
            field=models.ForeignKey(to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='input_ports',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='step_run', to='analysis.StepRunInputPort'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='output_ports',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='step_run', to='analysis.StepRunOutputPort'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='process_location',
            field=models.ForeignKey(to='analysis.ProcessLocation', null=True),
        ),
        migrations.AddField(
            model_name='steprun',
            name='step_definition',
            field=models.ForeignKey(related_name='step_runs', to='analysis.StepDefinition', null=True),
        ),
        migrations.AddField(
            model_name='steprun',
            name='steps',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='step_runs', to='analysis.Step'),
        ),
        migrations.AddField(
            model_name='stepresult',
            name='data_object',
            field=models.ForeignKey(related_name='step_results', to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='stepresult',
            name='output_port',
            field=models.OneToOneField(related_name='step_result', to='analysis.StepRunOutputPort'),
        ),
        migrations.AddField(
            model_name='stepdefinitioninputport',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='stepdefinitioninputport',
            name='file_names',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='port', to='analysis.FileName'),
        ),
        migrations.AddField(
            model_name='stepdefinition',
            name='environment',
            field=models.ForeignKey(to='analysis.StepDefinitionEnvironment'),
        ),
        migrations.AddField(
            model_name='stepdefinition',
            name='input_ports',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepDefinitionInputPort'),
        ),
        migrations.AddField(
            model_name='stepdefinition',
            name='output_ports',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.StepDefinitionOutputPort'),
        ),
        migrations.AddField(
            model_name='step',
            name='environment',
            field=models.OneToOneField(to='analysis.RequestEnvironment'),
        ),
        migrations.AddField(
            model_name='step',
            name='input_ports',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.RequestInputPort'),
        ),
        migrations.AddField(
            model_name='step',
            name='output_ports',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.RequestOutputPort'),
        ),
        migrations.AddField(
            model_name='step',
            name='resources',
            field=models.OneToOneField(to='analysis.RequestResourceSet'),
        ),
        migrations.AddField(
            model_name='step',
            name='step_definition',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.StepDefinition'),
        ),
        migrations.AddField(
            model_name='step',
            name='step_run',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.StepRun'),
        ),
        migrations.AddField(
            model_name='requestdatapipe',
            name='destination',
            field=models.ForeignKey(to='analysis.RequestDataPipeDestinationPortIdentifier'),
        ),
        migrations.AddField(
            model_name='requestdatapipe',
            name='source',
            field=models.ForeignKey(to='analysis.RequestDataPipeSourcePortIdentifier'),
        ),
        migrations.AddField(
            model_name='requestdatabinding',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='requestdatabinding',
            name='destination',
            field=models.ForeignKey(to='analysis.RequestDataBindingDestinationPortIdentifier'),
        ),
        migrations.AddField(
            model_name='filestoragelocation',
            name='file_contents',
            field=models.ForeignKey(to='analysis.FileContents', null=True),
        ),
    ]
