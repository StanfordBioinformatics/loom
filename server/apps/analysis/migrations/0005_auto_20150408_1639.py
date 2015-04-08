# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0004_auto_20150407_2118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisstatus',
            name='endtime',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 8, 16, 39, 46, 459809)),
        ),
        migrations.AlterField(
            model_name='analysisstatus',
            name='server',
            field=models.CharField(default=b'localhost', max_length=256),
        ),
        migrations.AlterField(
            model_name='analysisstatus',
            name='starttime',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 8, 16, 39, 46, 459781)),
        ),
    ]
