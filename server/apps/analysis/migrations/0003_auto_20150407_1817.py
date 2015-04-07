# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0002_auto_20150407_1636'),
    ]

    operations = [
        migrations.RenameField(
            model_name='analysis',
            old_name='pipelineid',
            new_name='pipeline',
        ),
    ]
