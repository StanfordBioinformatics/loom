# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='analysis',
            name='id',
        ),
        migrations.RemoveField(
            model_name='file',
            name='id',
        ),
        migrations.RemoveField(
            model_name='pipeline',
            name='id',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='id',
        ),
        migrations.RemoveField(
            model_name='session',
            name='id',
        ),
        migrations.RemoveField(
            model_name='step',
            name='id',
        ),
        migrations.AlterField(
            model_name='analysis',
            name='analysisid',
            field=models.CharField(max_length=256, serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='fileid',
            field=models.CharField(max_length=30, serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='pipelineid',
            field=models.CharField(max_length=256, serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='resourceid',
            field=models.IntegerField(default=0, serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='session',
            name='sessionid',
            field=models.CharField(max_length=256, serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='step',
            name='stepid',
            field=models.CharField(max_length=256, serialize=False, primary_key=True),
        ),
    ]
