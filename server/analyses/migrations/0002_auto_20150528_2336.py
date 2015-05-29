# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analyses', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessionrun',
            name='session_result',
        ),
        migrations.AddField(
            model_name='sessionresult',
            name='session_run',
            field=models.ForeignKey(default=0, to='analyses.SessionRun'),
            preserve_default=False,
        ),
    ]
