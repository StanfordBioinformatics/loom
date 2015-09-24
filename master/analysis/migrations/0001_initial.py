# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import immutable.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('hash_value', models.CharField(max_length=100)),
                ('hash_function', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileHandle',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileImportRequest',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('comments', models.CharField(max_length=10000)),
                ('requester', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileLocation',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProcessLocation',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataBinding',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataBindingPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
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
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestDataPipeDestinationPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
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
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
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
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestInputPort',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('name', models.CharField(max_length=256)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestOutputPort',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('name', models.CharField(max_length=256)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestResourceSet',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('memory', models.CharField(max_length=20)),
                ('cores', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestSubmission',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('requester', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('name', models.CharField(max_length=256)),
                ('command', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinition',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionDataBinding',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('file', models.ForeignKey(to='analysis.File')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionEnvironment',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionInputPort',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionOutputPort',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepDefinitionTemplate',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('command', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepResult',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepResultOutputBinding',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('file', models.ForeignKey(to='analysis.File')),
                ('output_port', models.ForeignKey(to='analysis.StepDefinitionOutputPort')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRun',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('is_complete', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=immutable.models.now)),
                ('datetime_updated', models.DateTimeField(default=immutable.models.now)),
                ('name', models.CharField(max_length=256, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkInProgress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('open_request_submissions', models.ManyToManyField(to='analysis.RequestSubmission')),
                ('open_workflows', models.ManyToManyField(to='analysis.Workflow')),
                ('steps_ready_to_run', models.ManyToManyField(related_name='ready_to_run_queue', to='analysis.StepRun')),
                ('steps_running', models.ManyToManyField(related_name='running_queue', to='analysis.StepRun')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileServerLocation',
            fields=[
                ('filelocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.FileLocation')),
                ('host_url', models.CharField(max_length=256)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.filelocation',),
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
            model_name='steprun',
            name='process_location',
            field=models.ForeignKey(to='analysis.ProcessLocation', null=True),
        ),
        migrations.AddField(
            model_name='steprun',
            name='step_definition',
            field=models.ForeignKey(to='analysis.StepDefinition'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='step_results',
            field=models.ManyToManyField(to='analysis.StepResult'),
        ),
        migrations.AddField(
            model_name='stepresult',
            name='output_binding',
            field=models.ForeignKey(to='analysis.StepResultOutputBinding'),
        ),
        migrations.AddField(
            model_name='stepresult',
            name='step_definition',
            field=models.ForeignKey(to='analysis.StepDefinition'),
        ),
        migrations.AddField(
            model_name='stepdefinitiontemplate',
            name='environment',
            field=models.ForeignKey(to='analysis.StepDefinitionEnvironment'),
        ),
        migrations.AddField(
            model_name='stepdefinitiontemplate',
            name='input_ports',
            field=models.ManyToManyField(to='analysis.StepDefinitionInputPort'),
        ),
        migrations.AddField(
            model_name='stepdefinitiontemplate',
            name='output_ports',
            field=models.ManyToManyField(to='analysis.StepDefinitionOutputPort'),
        ),
        migrations.AddField(
            model_name='stepdefinitiondatabinding',
            name='input_port',
            field=models.ForeignKey(to='analysis.StepDefinitionInputPort'),
        ),
        migrations.AddField(
            model_name='stepdefinition',
            name='data_bindings',
            field=models.ManyToManyField(to='analysis.StepDefinitionDataBinding'),
        ),
        migrations.AddField(
            model_name='stepdefinition',
            name='template',
            field=models.ForeignKey(to='analysis.StepDefinitionTemplate'),
        ),
        migrations.AddField(
            model_name='step',
            name='environment',
            field=models.ForeignKey(to='analysis.RequestEnvironment'),
        ),
        migrations.AddField(
            model_name='step',
            name='resources',
            field=models.ForeignKey(to='analysis.RequestResourceSet'),
        ),
        migrations.AddField(
            model_name='step',
            name='step_definition',
            field=models.ForeignKey(to='analysis.StepDefinition', null=True),
        ),
        migrations.AddField(
            model_name='step',
            name='step_run',
            field=models.ForeignKey(to='analysis.StepRun', null=True),
        ),
        migrations.AddField(
            model_name='step',
            name='workflow',
            field=models.ForeignKey(related_name='steps', to='analysis.Workflow', null=True),
        ),
        migrations.AddField(
            model_name='requestsubmission',
            name='workflows',
            field=models.ManyToManyField(to='analysis.Workflow'),
        ),
        migrations.AddField(
            model_name='requestoutputport',
            name='step',
            field=models.ForeignKey(related_name='output_ports', to='analysis.Step', null=True),
        ),
        migrations.AddField(
            model_name='requestinputport',
            name='step',
            field=models.ForeignKey(related_name='input_ports', to='analysis.Step', null=True),
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
            model_name='requestdatapipe',
            name='workflow',
            field=models.ForeignKey(related_name='data_pipes', to='analysis.Workflow', null=True),
        ),
        migrations.AddField(
            model_name='requestdatabinding',
            name='destination',
            field=models.ForeignKey(to='analysis.RequestDataBindingPortIdentifier'),
        ),
        migrations.AddField(
            model_name='requestdatabinding',
            name='file',
            field=models.ForeignKey(to='analysis.File'),
        ),
        migrations.AddField(
            model_name='requestdatabinding',
            name='workflow',
            field=models.ForeignKey(related_name='data_bindings', to='analysis.Workflow', null=True),
        ),
        migrations.AddField(
            model_name='filelocation',
            name='file',
            field=models.ForeignKey(to='analysis.File', null=True),
        ),
        migrations.AddField(
            model_name='fileimportrequest',
            name='file_location',
            field=models.ForeignKey(to='analysis.FileLocation'),
        ),
    ]
