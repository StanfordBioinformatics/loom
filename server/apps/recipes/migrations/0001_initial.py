# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Binding',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
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
            name='Location',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Port',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
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
            name='Run',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RunRecipe',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('input_bindings', models.ManyToManyField(to='recipes.Binding')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RunResult',
            fields=[
                ('_id', models.TextField(serialize=False, primary_key=True)),
                ('run_recipe', models.ForeignKey(to='recipes.RunRecipe')),
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
                ('location_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='recipes.Location')),
                ('storage_account', models.CharField(max_length=100)),
                ('container', models.CharField(max_length=100)),
                ('blob', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('recipes.location',),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('ingredient_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='recipes.Ingredient')),
            ],
            options={
                'abstract': False,
            },
            bases=('recipes.ingredient',),
        ),
        migrations.CreateModel(
            name='FilePathLocation',
            fields=[
                ('location_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='recipes.Location')),
                ('file_path', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('recipes.location',),
        ),
        migrations.CreateModel(
            name='FileRecipe',
            fields=[
                ('ingredient_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='recipes.Ingredient')),
            ],
            options={
                'abstract': False,
            },
            bases=('recipes.ingredient',),
        ),
        migrations.CreateModel(
            name='ImportRecipe',
            fields=[
                ('ingredient_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='recipes.Ingredient')),
            ],
            options={
                'abstract': False,
            },
            bases=('recipes.ingredient',),
        ),
        migrations.CreateModel(
            name='UrlLocation',
            fields=[
                ('location_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='recipes.Location')),
                ('url', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
            bases=('recipes.location',),
        ),
        migrations.AddField(
            model_name='session',
            name='steps',
            field=models.ManyToManyField(to='recipes.Step'),
        ),
        migrations.AddField(
            model_name='runrecipe',
            name='sessions',
            field=models.ManyToManyField(to='recipes.Session'),
        ),
        migrations.AddField(
            model_name='run',
            name='run_recipe',
            field=models.ForeignKey(to='recipes.RunRecipe'),
        ),
        migrations.AddField(
            model_name='run',
            name='run_result',
            field=models.ForeignKey(to='recipes.RunResult'),
        ),
        migrations.AddField(
            model_name='port',
            name='from_session',
            field=models.ForeignKey(to='recipes.Session'),
        ),
        migrations.AddField(
            model_name='import',
            name='import_result',
            field=models.ForeignKey(to='recipes.ImportResult'),
        ),
        migrations.AddField(
            model_name='binding',
            name='ingredient',
            field=models.ForeignKey(to='recipes.Ingredient'),
        ),
        migrations.AddField(
            model_name='binding',
            name='port',
            field=models.ForeignKey(to='recipes.Port'),
        ),
        migrations.AddField(
            model_name='runresult',
            name='input_file_recipes',
            field=models.ManyToManyField(to='recipes.FileRecipe'),
        ),
        migrations.AddField(
            model_name='runresult',
            name='input_files',
            field=models.ManyToManyField(related_name='inputs', to='recipes.File'),
        ),
        migrations.AddField(
            model_name='runresult',
            name='output_files',
            field=models.ManyToManyField(related_name='outputs', to='recipes.File'),
        ),
        migrations.AddField(
            model_name='request',
            name='file_recipes',
            field=models.ManyToManyField(to='recipes.FileRecipe'),
        ),
        migrations.AddField(
            model_name='importresult',
            name='file_imported',
            field=models.ForeignKey(to='recipes.File'),
        ),
        migrations.AddField(
            model_name='importresult',
            name='import_recipe',
            field=models.ForeignKey(to='recipes.ImportRecipe'),
        ),
        migrations.AddField(
            model_name='importrequest',
            name='import_recipe',
            field=models.ForeignKey(to='recipes.ImportRecipe'),
        ),
        migrations.AddField(
            model_name='importrecipe',
            name='destination',
            field=models.ForeignKey(related_name='destination', to='recipes.Location'),
        ),
        migrations.AddField(
            model_name='importrecipe',
            name='source',
            field=models.ForeignKey(related_name='source', to='recipes.Location'),
        ),
        migrations.AddField(
            model_name='import',
            name='import_recipe',
            field=models.ForeignKey(to='recipes.ImportRecipe'),
        ),
        migrations.AddField(
            model_name='filerecipe',
            name='from_port',
            field=models.ForeignKey(to='recipes.Port'),
        ),
        migrations.AddField(
            model_name='filerecipe',
            name='from_run_recipe',
            field=models.ForeignKey(to='recipes.RunRecipe'),
        ),
        migrations.AddField(
            model_name='file',
            name='location',
            field=models.ForeignKey(to='recipes.Location'),
        ),
    ]
