# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
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
            name='AbstractWorkflowInput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
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
                ('rename', models.CharField(max_length=255)),
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
                ('rename', models.CharField(max_length=255)),
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
            name='WorkflowOutput',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('from_channel', models.CharField(max_length=255)),
                ('rename', models.CharField(max_length=255)),
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
                ('input_name', models.CharField(max_length=255)),
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
            name='WorkflowInput',
            fields=[
                ('abstractworkflowinput_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflowInput')),
                ('to_channel', models.CharField(max_length=255)),
                ('data_object', models.ForeignKey(to='analysis.DataObject')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflowinput',),
        ),
        migrations.CreateModel(
            name='WorkflowInputPlaceholder',
            fields=[
                ('abstractworkflowinput_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflowInput')),
                ('input_name', models.CharField(max_length=255)),
                ('to_channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'file', b'File'), (b'file_array', b'File Array'), (b'boolean', b'Boolean'), (b'boolean_array', b'Boolean Array'), (b'string', b'String'), (b'string_array', b'String Array'), (b'integer', b'Integer'), (b'integer_array', b'Integer Array'), (b'float', b'Float'), (b'float_array', b'Float Array'), (b'json', b'JSON'), (b'json_array', b'JSON Array')])),
                ('prompt', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflowinput',),
        ),
        migrations.AddField(
            model_name='workflowruninput',
            name='data_object',
            field=models.ForeignKey(to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.WorkflowRunInput'),
        ),
        migrations.AddField(
            model_name='workflowrun',
            name='workflow',
            field=models.ForeignKey(to='analysis.Workflow'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='workflow_inputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.AbstractWorkflowInput'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='workflow_outputs',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='analysis.WorkflowOutput'),
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
            model_name='dataobjectarray',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='parent', to='analysis.DataObject'),
        ),
    ]
