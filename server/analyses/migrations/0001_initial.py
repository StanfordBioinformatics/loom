# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisRequest',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('requester', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnalysisRun',
            fields=[
                ('_id', models.AutoField(serialize=False, primary_key=True)),
                ('analysis_request', models.ForeignKey(to='analyses.AnalysisRequest')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnalysisRunRecord',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('analysis_request', models.ForeignKey(to='analyses.AnalysisRequest')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileImportRecord',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('import_comments', models.CharField(max_length=10000)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileImportRun',
            fields=[
                ('_id', models.AutoField(serialize=False, primary_key=True)),
                ('import_comments', models.CharField(max_length=10000)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileLocation',
            fields=[
                ('_id', models.AutoField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InputBinding',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InputPort',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OutputPort',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResourceSet',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('memory_bytes', models.BigIntegerField()),
                ('cores', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('input_bindings', models.ManyToManyField(to='analyses.InputBinding')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRun',
            fields=[
                ('_id', models.AutoField(serialize=False, primary_key=True)),
                ('step', models.ForeignKey(to='analyses.Step')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepRunRecord',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('step', models.ForeignKey(to='analyses.Step')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StepTemplate',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('command', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AzureBlobLocation',
            fields=[
                ('filelocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.FileLocation')),
                ('storage_account', models.CharField(max_length=100)),
                ('container', models.CharField(max_length=100)),
                ('blob', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.filelocation',),
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
            bases=('analyses.environment',),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.DataObject')),
                ('hash_value', models.CharField(max_length=100)),
                ('hash_function', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.dataobject',),
        ),
        migrations.CreateModel(
            name='FilePathLocation',
            fields=[
                ('filelocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.FileLocation')),
                ('file_path', models.CharField(max_length=256)),
                ('file', models.ForeignKey(to='analyses.File')),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.filelocation',),
        ),
        migrations.CreateModel(
            name='FileRecipe',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.DataObject')),
                ('output_port', models.ForeignKey(to='analyses.OutputPort')),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.dataobject',),
        ),
        migrations.CreateModel(
            name='UrlLocation',
            fields=[
                ('filelocation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.FileLocation')),
                ('url', models.CharField(max_length=256)),
                ('file', models.ForeignKey(to='analyses.File')),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.filelocation',),
        ),
        migrations.AddField(
            model_name='steptemplate',
            name='environment',
            field=models.ForeignKey(to='analyses.Environment'),
        ),
        migrations.AddField(
            model_name='steptemplate',
            name='input_ports',
            field=models.ManyToManyField(related_name='step_templates', to='analyses.InputPort'),
        ),
        migrations.AddField(
            model_name='steptemplate',
            name='output_ports',
            field=models.ManyToManyField(related_name='step_templates', to='analyses.OutputPort'),
        ),
        migrations.AddField(
            model_name='steprun',
            name='step_run_record',
            field=models.ForeignKey(to='analyses.StepRunRecord', null=True),
        ),
        migrations.AddField(
            model_name='step',
            name='step_template',
            field=models.ForeignKey(to='analyses.StepTemplate'),
        ),
        migrations.AddField(
            model_name='resourceset',
            name='step',
            field=models.ForeignKey(to='analyses.Step'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='data_object',
            field=models.ForeignKey(to='analyses.DataObject'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='input_port',
            field=models.ForeignKey(to='analyses.InputPort'),
        ),
        migrations.AddField(
            model_name='fileimportrun',
            name='destination',
            field=models.ForeignKey(to='analyses.FileLocation'),
        ),
        migrations.AddField(
            model_name='fileimportrun',
            name='file_import_record',
            field=models.ForeignKey(to='analyses.FileImportRecord', null=True),
        ),
        migrations.AddField(
            model_name='analysisrunrecord',
            name='step_run_records',
            field=models.ManyToManyField(to='analyses.StepRunRecord'),
        ),
        migrations.AddField(
            model_name='analysisrun',
            name='analysis_run_record',
            field=models.ForeignKey(to='analyses.AnalysisRunRecord', null=True),
        ),
        migrations.AddField(
            model_name='analysisrequest',
            name='resource_sets',
            field=models.ManyToManyField(to='analyses.ResourceSet'),
        ),
        migrations.AddField(
            model_name='steprunrecord',
            name='file',
            field=models.ForeignKey(to='analyses.File'),
        ),
        migrations.AddField(
            model_name='filerecipe',
            name='step',
            field=models.ForeignKey(to='analyses.Step'),
        ),
        migrations.AddField(
            model_name='fileimportrecord',
            name='file',
            field=models.ForeignKey(to='analyses.File'),
        ),
        migrations.AddField(
            model_name='azurebloblocation',
            name='file',
            field=models.ForeignKey(to='analyses.File'),
        ),
        migrations.AddField(
            model_name='analysisrequest',
            name='file_recipes',
            field=models.ManyToManyField(to='analyses.FileRecipe'),
        ),
    ]
