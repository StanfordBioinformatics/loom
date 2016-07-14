# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractFileImport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('is_closed_to_new_data', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChannelOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataObjectContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=1000)),
                ('status', models.CharField(default=b'incomplete', max_length=256, choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InputOutputNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_analysis.inputoutputnode_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UnnamedFileContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash_value', models.CharField(max_length=255)),
                ('hash_function', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BooleanDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('boolean_value', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='BooleanDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('boolean_content', models.ForeignKey(to='analysis.BooleanDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='DataObjectArray',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='FileContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('filename', models.CharField(max_length=255)),
                ('unnamed_file_content', models.ForeignKey(to='analysis.UnnamedFileContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('file_content', models.ForeignKey(to='analysis.FileContent', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='FileImport',
            fields=[
                ('abstractfileimport_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.AbstractFileImport')),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.abstractfileimport',),
        ),
        migrations.CreateModel(
            name='IntegerDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('integer_value', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='IntegerDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('integer_content', models.ForeignKey(to='analysis.IntegerDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='JSONDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('json_value', jsonfield.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='JSONDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('json_content', models.ForeignKey(to='analysis.JSONDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='StringDataContent',
            fields=[
                ('dataobjectcontent_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObjectContent')),
                ('string_value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobjectcontent',),
        ),
        migrations.CreateModel(
            name='StringDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='analysis.DataObject')),
                ('string_content', models.ForeignKey(to='analysis.StringDataContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.AddField(
            model_name='filelocation',
            name='unnamed_file_content',
            field=models.ForeignKey(related_name='file_locations', to='analysis.UnnamedFileContent', null=True),
        ),
        migrations.AddField(
            model_name='dataobjectcontent',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_analysis.dataobjectcontent_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='dataobject',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_analysis.dataobject_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='channeloutput',
            name='data_objects',
            field=models.ManyToManyField(to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='channeloutput',
            name='receiver',
            field=models.OneToOneField(related_name='from_channel', null=True, to='analysis.InputOutputNode'),
        ),
        migrations.AddField(
            model_name='channel',
            name='data_objects',
            field=models.ManyToManyField(to='analysis.DataObject'),
        ),
        migrations.AddField(
            model_name='channel',
            name='sender',
            field=models.OneToOneField(related_name='to_channel', null=True, to='analysis.InputOutputNode'),
        ),
        migrations.AddField(
            model_name='abstractfileimport',
            name='file_location',
            field=models.ForeignKey(related_name='file_imports', to='analysis.FileLocation', null=True),
        ),
        migrations.AddField(
            model_name='abstractfileimport',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_analysis.abstractfileimport_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='abstractfileimport',
            name='temp_file_location',
            field=models.OneToOneField(related_name='temp_file_import', null=True, to='analysis.FileLocation'),
        ),
        migrations.AddField(
            model_name='filedataobject',
            name='file_import',
            field=models.OneToOneField(related_name='data_object', to='analysis.AbstractFileImport'),
        ),
        migrations.AddField(
            model_name='dataobjectarray',
            name='items',
            field=models.ManyToManyField(related_name='container', to='analysis.DataObject'),
        ),
    ]
