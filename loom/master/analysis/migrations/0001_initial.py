# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import sortedone2many.fields
import django.utils.timezone
import uuid
import sortedm2m.fields
import analysis.models.common


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractDataObject',
            fields=[
                ('_id', models.CharField(max_length=255, serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='AbstractWorkflowInput',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='DataSourceRecord',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('source_description', models.TextField(max_length=10000)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
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
            bases=(models.Model, analysis.models.common._ClassNameMixin),
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
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='RequestedEnvironment',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='RequestedResourceSet',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('memory', models.CharField(max_length=255)),
                ('disk_space', models.CharField(max_length=255)),
                ('cores', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('step_name', models.CharField(max_length=255)),
                ('command', models.CharField(max_length=255)),
                ('interpreter', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='StepInput',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('from_channel', models.CharField(max_length=255)),
                ('to_path', models.CharField(max_length=255)),
                ('rename', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='StepOutput',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('from_path', models.CharField(max_length=255)),
                ('to_channel', models.CharField(max_length=255)),
                ('rename', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('workflow_name', models.CharField(max_length=255)),
                ('force_rerun', models.BooleanField(default=False)),
                ('steps', sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow', to='analysis.Step')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='WorkflowOutput',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('from_channel', models.CharField(max_length=255)),
                ('rename', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='WorkflowRunRequest',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='WorkflowRunRequestInput',
            fields=[
                ('_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('input_name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.common._ClassNameMixin),
        ),
        migrations.CreateModel(
            name='DataObjectArray',
            fields=[
                ('abstractdataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractDataObject')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractdataobject',),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('abstractdataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractDataObject')),
                ('file_name', models.CharField(max_length=255)),
                ('metadata', jsonfield.fields.JSONField()),
                ('file_contents', models.ForeignKey(to='analysis.FileContents')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractdataobject',),
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
            name='JSONDataObject',
            fields=[
                ('abstractdataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractDataObject')),
                ('name', models.CharField(max_length=256)),
                ('json_data', jsonfield.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractdataobject',),
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
            name='WorkflowInput',
            fields=[
                ('abstractworkflowinput_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractWorkflowInput')),
                ('to_channel', models.CharField(max_length=255)),
                ('data_object', models.ForeignKey(to='analysis.AbstractDataObject')),
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
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractworkflowinput',),
        ),
        migrations.AddField(
            model_name='workflowrunrequestinput',
            name='data_object',
            field=models.ForeignKey(to='analysis.AbstractDataObject'),
        ),
        migrations.AddField(
            model_name='workflowrunrequest',
            name='inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow_run_request', to='analysis.WorkflowRunRequestInput'),
        ),
        migrations.AddField(
            model_name='workflowrunrequest',
            name='workflow',
            field=models.ForeignKey(related_name='workflow_run_requests', to='analysis.Workflow'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='workflow_inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow', to='analysis.AbstractWorkflowInput'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='workflow_outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, related_name='workflow', to='analysis.WorkflowOutput'),
        ),
        migrations.AddField(
            model_name='step',
            name='environment',
            field=models.OneToOneField(to='analysis.RequestedEnvironment'),
        ),
        migrations.AddField(
            model_name='step',
            name='resources',
            field=models.OneToOneField(to='analysis.RequestedResourceSet'),
        ),
        migrations.AddField(
            model_name='step',
            name='step_inputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.StepInput'),
        ),
        migrations.AddField(
            model_name='step',
            name='step_outputs',
            field=sortedone2many.fields.SortedOneToManyField(help_text=None, to='analysis.StepOutput'),
        ),
        migrations.AddField(
            model_name='filestoragelocation',
            name='file_contents',
            field=models.ForeignKey(related_name='file_storage_locations', to='analysis.FileContents', null=True),
        ),
        migrations.AddField(
            model_name='datasourcerecord',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='data_source_record', to='analysis.AbstractDataObject'),
        ),
        migrations.AddField(
            model_name='dataobjectarray',
            name='data_objects',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='parent', to='analysis.AbstractDataObject'),
        ),
    ]
