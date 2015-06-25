# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
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
                ('analyses', models.ManyToManyField(to='analysis.Analysis')),
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
            name='WorkInProgress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('new_analyses', models.ManyToManyField(to='analysis.Analysis')),
                ('new_steps', models.ManyToManyField(to='analysis.Step')),
                ('open_requests', models.ManyToManyField(to='analysis.Request')),
            ],
        ),
        migrations.CreateModel(
            name='DockerImage',
            fields=[
                ('environment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.Environment')),
                ('docker_image', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.environment', models.Model),
        ),
        migrations.AddField(
            model_name='step',
            name='environment',
            field=models.ForeignKey(to='analysis.Environment'),
        ),
        migrations.AddField(
            model_name='step',
            name='input_ports',
            field=models.ManyToManyField(to='analysis.InputPort'),
        ),
        migrations.AddField(
            model_name='step',
            name='output_ports',
            field=models.ManyToManyField(to='analysis.OutputPort'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='destination',
            field=models.ForeignKey(to='analysis.InputBindingDestination'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='file',
            field=models.ForeignKey(to='analysis.File'),
        ),
        migrations.AddField(
            model_name='connector',
            name='destination',
            field=models.ForeignKey(to='analysis.DestinationStepAndPort'),
        ),
        migrations.AddField(
            model_name='connector',
            name='source',
            field=models.ForeignKey(to='analysis.SourceStepAndPort'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='connectors',
            field=models.ManyToManyField(to='analysis.Connector'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='input_bindings',
            field=models.ManyToManyField(to='analysis.InputBinding'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='steps',
            field=models.ManyToManyField(to='analysis.Step'),
        ),
    ]
