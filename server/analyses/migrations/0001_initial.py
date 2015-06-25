# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisDefinition',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Connector',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DestinationStepAndPort',
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
            name='Environment',
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
            name='InputBinding',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InputBindingDestination',
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
            name='InputPort',
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
            name='OutputPort',
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
            name='Request',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('requester', models.CharField(max_length=100)),
                ('analysis_definitions', models.ManyToManyField(to='analyses.AnalysisDefinition')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SourceStepAndPort',
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
            name='Step',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('command', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DockerImage',
            fields=[
                ('environment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.Environment')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.environment', models.Model),
        ),
        migrations.AddField(
            model_name='step',
            name='environment',
            field=models.ForeignKey(to='analyses.Environment'),
        ),
        migrations.AddField(
            model_name='step',
            name='input_ports',
            field=models.ManyToManyField(to='analyses.InputPort'),
        ),
        migrations.AddField(
            model_name='step',
            name='output_ports',
            field=models.ManyToManyField(to='analyses.OutputPort'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='destination',
            field=models.ForeignKey(to='analyses.InputBindingDestination'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='file',
            field=models.ForeignKey(to='analyses.File'),
        ),
        migrations.AddField(
            model_name='connector',
            name='destination',
            field=models.ForeignKey(to='analyses.DestinationStepAndPort'),
        ),
        migrations.AddField(
            model_name='connector',
            name='source',
            field=models.ForeignKey(to='analyses.SourceStepAndPort'),
        ),
        migrations.AddField(
            model_name='analysisdefinition',
            name='connectors',
            field=models.ManyToManyField(to='analyses.Connector'),
        ),
        migrations.AddField(
            model_name='analysisdefinition',
            name='input_bindings',
            field=models.ManyToManyField(to='analyses.InputBinding'),
        ),
        migrations.AddField(
            model_name='analysisdefinition',
            name='steps',
            field=models.ManyToManyField(to='analyses.Step'),
        ),
    ]
