# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisRequest',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnalysisRun',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('analysis_request', models.ForeignKey(to='analysis.AnalysisRequest')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EnvironmentRequest',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
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
            name='FileImportRequest',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('import_comments', models.CharField(max_length=10000)),
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
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InputBindingPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('step', models.CharField(max_length=256)),
                ('port', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OutputBinding',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('file', models.ForeignKey(to='analysis.File')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('requester', models.CharField(max_length=100)),
                ('analyses', models.ManyToManyField(to='analysis.AnalysisRequest')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestConnector',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestConnectorDestinationPortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('step', models.CharField(max_length=256)),
                ('port', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestConnectorSourcePortIdentifier',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('step', models.CharField(max_length=256)),
                ('port', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestInputBinding',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('destination', models.ForeignKey(to='analysis.InputBindingPortIdentifier')),
                ('file', models.ForeignKey(to='analysis.File')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RequestInputPort',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
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
                ('name', models.CharField(max_length=256)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResourceRequest',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('memory', models.CharField(max_length=20)),
                ('cores', models.IntegerField()),
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
            name='StepRequest',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('command', models.CharField(max_length=256)),
                ('analysis_request', models.ForeignKey(related_name='steps', to='analysis.AnalysisRequest', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepResult',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('output_bindings', models.ManyToManyField(to='analysis.OutputBinding')),
                ('step_definition', models.ForeignKey(to='analysis.StepDefinition')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRun',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('step', models.ForeignKey(to='analysis.StepDefinition')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkInProgress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('open_requests', models.ManyToManyField(to='analysis.Request')),
                ('ready_analyses', models.ManyToManyField(to='analysis.AnalysisRequest')),
                ('ready_steps', models.ManyToManyField(to='analysis.StepRequest')),
                ('running_analyses', models.ManyToManyField(to='analysis.AnalysisRun')),
                ('running_steps', models.ManyToManyField(to='analysis.StepRun')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DockerImageRequest',
            fields=[
                ('environmentrequest_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.EnvironmentRequest')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.environmentrequest',),
        ),
        migrations.CreateModel(
            name='FilePathLocation',
            fields=[
                ('filelocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.FileLocation')),
                ('file_path', models.CharField(max_length=256)),
                ('file', models.ForeignKey(to='analysis.File', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.filelocation',),
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
            model_name='steprequest',
            name='environment',
            field=models.ForeignKey(to='analysis.EnvironmentRequest'),
        ),
        migrations.AddField(
            model_name='steprequest',
            name='resources',
            field=models.ForeignKey(to='analysis.ResourceRequest'),
        ),
        migrations.AddField(
            model_name='steprequest',
            name='step',
            field=models.ForeignKey(to='analysis.StepDefinition', null=True),
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
            model_name='requestoutputport',
            name='step_request',
            field=models.ForeignKey(related_name='output_ports', to='analysis.StepRequest', null=True),
        ),
        migrations.AddField(
            model_name='requestinputport',
            name='step_request',
            field=models.ForeignKey(related_name='input_ports', to='analysis.StepRequest', null=True),
        ),
        migrations.AddField(
            model_name='requestconnector',
            name='destination',
            field=models.ForeignKey(to='analysis.RequestConnectorDestinationPortIdentifier'),
        ),
        migrations.AddField(
            model_name='requestconnector',
            name='source',
            field=models.ForeignKey(to='analysis.RequestConnectorSourcePortIdentifier'),
        ),
        migrations.AddField(
            model_name='outputbinding',
            name='output_port',
            field=models.ForeignKey(to='analysis.StepDefinitionOutputPort'),
        ),
        migrations.AddField(
            model_name='fileimportrequest',
            name='file_location',
            field=models.ForeignKey(to='analysis.FileLocation'),
        ),
        migrations.AddField(
            model_name='analysisrun',
            name='step_runs',
            field=models.ManyToManyField(to='analysis.StepRun'),
        ),
        migrations.AddField(
            model_name='analysisrequest',
            name='connectors',
            field=models.ManyToManyField(to='analysis.RequestConnector'),
        ),
        migrations.AddField(
            model_name='analysisrequest',
            name='input_bindings',
            field=models.ManyToManyField(to='analysis.RequestInputBinding'),
        ),
    ]
