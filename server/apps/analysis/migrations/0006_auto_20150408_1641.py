# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0005_auto_20150408_1639'),
    ]

    operations = [
        migrations.RenameField(
            model_name='analysis',
            old_name='pipeline',
            new_name='pipelineid',
        ),
        migrations.AlterField(
            model_name='analysisstatus',
            name='endtime',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 8, 16, 41, 34, 856215)),
        ),
        migrations.AlterField(
            model_name='analysisstatus',
            name='starttime',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 8, 16, 41, 34, 856189)),
        ),
    ]
