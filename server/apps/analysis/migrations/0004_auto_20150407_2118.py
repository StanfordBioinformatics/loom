# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0003_auto_20150407_1817'),
    ]

    operations = [
        migrations.RenameField(
            model_name='analysisstatus',
            old_name='serverid',
            new_name='server',
        ),
        migrations.RemoveField(
            model_name='analysisstatus',
            name='id',
        ),
        migrations.AddField(
            model_name='analysisstatus',
            name='analysis',
            field=models.ForeignKey(to='analysis.Analysis', null=True),
        ),
        migrations.AddField(
            model_name='analysisstatus',
            name='statusid',
            field=models.CharField(default='', max_length=256, serialize=False, primary_key=True),
            preserve_default=False,
        ),
    ]
