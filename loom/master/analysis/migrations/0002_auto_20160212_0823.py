# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filestoragelocation',
            name='file_contents',
            field=models.ForeignKey(related_name='file_storage_locations', to='analysis.FileContents', null=True),
        ),
    ]
