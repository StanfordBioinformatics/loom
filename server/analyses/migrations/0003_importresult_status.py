# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analyses', '0002_auto_20150528_2336'),
    ]

    operations = [
        migrations.AddField(
            model_name='importresult',
            name='status',
            field=models.CharField(default='', max_length=16),
            preserve_default=False,
        ),
    ]
