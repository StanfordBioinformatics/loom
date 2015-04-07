# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('analysisid', models.CharField(max_length=256)),
                ('comment', models.CharField(max_length=256)),
                ('ownerid', models.IntegerField(default=0)),
                ('access', models.IntegerField(default=755)),
            ],
        ),
        migrations.CreateModel(
            name='AnalysisStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('serverid', models.CharField(max_length=256)),
                ('starttime', models.DateTimeField()),
                ('endtime', models.DateTimeField()),
                ('retries', models.IntegerField(default=0)),
                ('ramusage', models.IntegerField(default=0)),
                ('coresusage', models.IntegerField(default=1)),
                ('msg', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fileid', models.CharField(max_length=30)),
                ('uri', models.CharField(max_length=256)),
                ('ownerid', models.IntegerField(default=0)),
                ('access', models.IntegerField(default=755)),
                ('comment', models.CharField(default=b'', max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Pipeline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pipelineid', models.CharField(max_length=256)),
                ('pipelinename', models.CharField(max_length=30)),
                ('comment', models.CharField(default=b'', max_length=256)),
                ('access', models.IntegerField(default=755)),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resourceid', models.IntegerField(default=0)),
                ('diskspace', models.IntegerField(default=1000)),
                ('memory', models.IntegerField(default=1000)),
                ('cores', models.IntegerField(default=1)),
                ('ownerid', models.IntegerField(default=0)),
                ('access', models.IntegerField(default=755)),
                ('comment', models.CharField(default=b'', max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sessionid', models.CharField(max_length=256)),
                ('sessionname', models.CharField(max_length=30)),
                ('comment', models.CharField(default=b'', max_length=256)),
                ('access', models.IntegerField(default=755)),
                ('importfiles', models.ManyToManyField(related_name='infile_id', to='analysis.File')),
                ('resourceid', models.ForeignKey(blank=True, to='analysis.Resource', null=True)),
                ('savefiles', models.ManyToManyField(related_name='outfile_id', to='analysis.File')),
            ],
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stepid', models.CharField(max_length=256)),
                ('stepname', models.CharField(max_length=30)),
                ('cmd', models.CharField(max_length=256)),
                ('application', models.CharField(max_length=256)),
                ('comment', models.CharField(default=b'', max_length=256)),
                ('access', models.IntegerField(default=755)),
            ],
        ),
        migrations.AddField(
            model_name='session',
            name='steps',
            field=models.ManyToManyField(related_name='step_id', to='analysis.Step'),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='sessionids',
            field=models.ManyToManyField(related_name='session_id', to='analysis.Session'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='pipelineid',
            field=models.ForeignKey(to='analysis.Pipeline'),
        ),
    ]
