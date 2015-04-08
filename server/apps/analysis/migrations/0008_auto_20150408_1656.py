# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0007_auto_20150408_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysisstatus',
            name='endtime',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 8, 16, 56, 37, 729817)),
        ),
        migrations.AlterField(
            model_name='analysisstatus',
            name='starttime',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 8, 16, 56, 37, 729790)),
        ),
    ]
