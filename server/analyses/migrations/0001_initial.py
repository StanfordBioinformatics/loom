# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Hash',
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
            name='Import',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportRequest',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ImportResult',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
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
            name='Location',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
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
            name='Request',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('date', models.DateTimeField()),
                ('requester', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SessionRecipe',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('input_bindings', models.ManyToManyField(to='analyses.InputBinding')),
                ('sessions', models.ManyToManyField(to='analyses.Session')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SessionResult',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('session_recipe', models.ForeignKey(to='analyses.SessionRecipe')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SessionRun',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('session_recipe', models.ForeignKey(to='analyses.SessionRecipe')),
                ('session_result', models.ForeignKey(to='analyses.SessionResult')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('docker_image', models.CharField(max_length=100)),
                ('command', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BlobLocation',
            fields=[
                ('location_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.Location')),
                ('storage_account', models.CharField(max_length=100)),
                ('container', models.CharField(max_length=100)),
                ('blob', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.location',),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('ingredient_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.Ingredient')),
                ('hash', models.ForeignKey(to='analyses.Hash')),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.ingredient',),
        ),
        migrations.CreateModel(
            name='FilePathLocation',
            fields=[
                ('location_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.Location')),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.location',),
        ),
        migrations.CreateModel(
            name='FileRecipe',
            fields=[
                ('ingredient_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.Ingredient')),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.ingredient',),
        ),
        migrations.CreateModel(
            name='ImportRecipe',
            fields=[
                ('ingredient_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.Ingredient')),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.ingredient',),
        ),
        migrations.CreateModel(
            name='UrlLocation',
            fields=[
                ('location_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analyses.Location')),
                ('url', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('analyses.location',),
        ),
        migrations.AddField(
            model_name='session',
            name='steps',
            field=models.ManyToManyField(to='analyses.Step'),
        ),
        migrations.AddField(
            model_name='outputport',
            name='session',
            field=models.ForeignKey(to='analyses.Session'),
        ),
        migrations.AddField(
            model_name='inputport',
            name='session',
            field=models.ForeignKey(to='analyses.Session'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='ingredient',
            field=models.ForeignKey(to='analyses.Ingredient'),
        ),
        migrations.AddField(
            model_name='inputbinding',
            name='input_port',
            field=models.ForeignKey(to='analyses.InputPort'),
        ),
        migrations.AddField(
            model_name='import',
            name='import_result',
            field=models.ForeignKey(to='analyses.ImportResult'),
        ),
        migrations.AddField(
            model_name='sessionresult',
            name='input_file_recipes',
            field=models.ManyToManyField(to='analyses.FileRecipe'),
        ),
        migrations.AddField(
            model_name='sessionresult',
            name='input_files',
            field=models.ManyToManyField(related_name='inputs', to='analyses.File'),
        ),
        migrations.AddField(
            model_name='sessionresult',
            name='output_files',
            field=models.ManyToManyField(related_name='outputs', to='analyses.File'),
        ),
        migrations.AddField(
            model_name='request',
            name='file_recipes',
            field=models.ManyToManyField(to='analyses.FileRecipe'),
        ),
        migrations.AddField(
            model_name='importresult',
            name='file_imported',
            field=models.ForeignKey(to='analyses.File'),
        ),
        migrations.AddField(
            model_name='importresult',
            name='import_recipe',
            field=models.ForeignKey(to='analyses.ImportRecipe'),
        ),
        migrations.AddField(
            model_name='importrequest',
            name='import_recipe',
            field=models.ForeignKey(to='analyses.ImportRecipe'),
        ),
        migrations.AddField(
            model_name='importrecipe',
            name='destination',
            field=models.ForeignKey(related_name='destination', to='analyses.Location'),
        ),
        migrations.AddField(
            model_name='importrecipe',
            name='source',
            field=models.ForeignKey(related_name='source', to='analyses.Location'),
        ),
        migrations.AddField(
            model_name='import',
            name='import_recipe',
            field=models.ForeignKey(to='analyses.ImportRecipe'),
        ),
        migrations.AddField(
            model_name='filerecipe',
            name='port',
            field=models.ForeignKey(to='analyses.OutputPort'),
        ),
        migrations.AddField(
            model_name='filerecipe',
            name='session_recipe',
            field=models.ForeignKey(to='analyses.SessionRecipe'),
        ),
        migrations.AddField(
            model_name='file',
            name='location',
            field=models.ForeignKey(to='analyses.Location'),
        ),
    ]
