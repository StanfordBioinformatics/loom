# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import analysis.models.base
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('loom_id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelNameMixin, analysis.models.base._SignalMixin, analysis.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataObjectContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelNameMixin, analysis.models.base._SignalMixin, analysis.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FileImport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, analysis.models.base._ModelNameMixin, analysis.models.base._SignalMixin, analysis.models.base._FilterMixin),
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
            bases=(models.Model, analysis.models.base._ModelNameMixin, analysis.models.base._SignalMixin, analysis.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='UnnamedFileContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash_value', models.CharField(max_length=255)),
                ('hash_function', models.CharField(max_length=255)),
            ],
            bases=(models.Model, analysis.models.base._ModelNameMixin, analysis.models.base._SignalMixin, analysis.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='BooleanContent',
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
                ('boolean_content', models.OneToOneField(related_name='data_object', on_delete=django.db.models.deletion.PROTECT, to='analysis.BooleanContent')),
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
                ('file_content', models.ForeignKey(related_name='file_data_object', on_delete=django.db.models.deletion.PROTECT, to='analysis.FileContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='IntegerContent',
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
                ('integer_content', models.OneToOneField(related_name='data_object', on_delete=django.db.models.deletion.PROTECT, to='analysis.IntegerContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.CreateModel(
            name='StringContent',
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
                ('string_content', models.OneToOneField(related_name='data_object', on_delete=django.db.models.deletion.PROTECT, to='analysis.StringContent')),
            ],
            options={
                'abstract': False,
            },
            bases=('analysis.dataobject',),
        ),
        migrations.AlterUniqueTogether(
            name='unnamedfilecontent',
            unique_together=set([('hash_value', 'hash_function')]),
        ),
        migrations.AddField(
            model_name='filelocation',
            name='unnamed_file_content',
            field=models.ForeignKey(related_name='file_locations', on_delete=django.db.models.deletion.SET_NULL, to='analysis.UnnamedFileContent', null=True),
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
            model_name='fileimport',
            name='file_data_object',
            field=models.OneToOneField(related_name='file_import', to='analysis.FileDataObject'),
        ),
        migrations.AddField(
            model_name='filedataobject',
            name='file_location',
            field=models.ForeignKey(related_name='file_data_object', on_delete=django.db.models.deletion.PROTECT, to='analysis.FileLocation'),
        ),
        migrations.AddField(
            model_name='filecontent',
            name='unnamed_file_content',
            field=models.ForeignKey(related_name='file_contents', on_delete=django.db.models.deletion.PROTECT, to='analysis.UnnamedFileContent'),
        ),
    ]
