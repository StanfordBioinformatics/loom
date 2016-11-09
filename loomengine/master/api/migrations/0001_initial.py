# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import api.models.base
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArrayMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField(null=True)),
                ('degree', models.IntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
                ('is_array', models.BooleanField(default=False)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FileResource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('file_url', models.CharField(max_length=1000)),
                ('md5', models.CharField(max_length=255)),
                ('upload_status', models.CharField(default=b'incomplete', max_length=255, choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FixedStepInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
                ('channel', models.CharField(max_length=255)),
                ('mode', models.CharField(default=b'no_gather', max_length=255)),
                ('group', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='FixedWorkflowInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
                ('channel', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='InputOutputNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('data_root', models.ForeignKey(related_name='input_output_nodes', to='api.DataNode', null=True)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_api.inputoutputnode_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RequestedEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RequestedResourceSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('memory', models.CharField(max_length=255, null=True)),
                ('disk_size', models.CharField(max_length=255, null=True)),
                ('cores', models.CharField(max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='StepInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
                ('channel', models.CharField(max_length=255)),
                ('mode', models.CharField(default=b'no_gather', max_length=255)),
                ('group', models.IntegerField(default=0)),
                ('hint', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StepOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
                ('mode', models.CharField(default=b'no_scatter', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='StepOutputSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=1024, null=True)),
                ('stream', models.CharField(max_length=255, null=True)),
                ('output', models.OneToOneField(related_name='source', to='api.StepOutput')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(null=True)),
                ('interpreter', models.CharField(default=b'/bin/bash', max_length=255)),
                ('command', models.TextField()),
                ('rendered_command', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(null=True)),
                ('last_heartbeat', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(default=b'Not started', max_length=255)),
                ('task', models.ForeignKey(related_name='task_attempts', to='api.Task')),
                ('task_as_accepted_attempt', models.OneToOneField(related_name='accepted_task_attempt', null=True, to='api.Task')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=255)),
                ('detail', models.TextField(null=True, blank=True)),
                ('task_attempt', models.ForeignKey(related_name='errors', to='api.TaskAttempt')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptLogFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('log_name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskEnvironment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'docker', b'Docker')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskOutputSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=255)),
                ('stream', models.CharField(max_length=255, choices=[(b'stdout', b'stdout'), (b'sterr', b'stderr')])),
                ('task_output', models.OneToOneField(related_name='source', to='api.TaskOutput')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskResourceSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('memory', models.CharField(max_length=255, null=True)),
                ('disk_size', models.CharField(max_length=255, null=True)),
                ('cores', models.CharField(max_length=255, null=True)),
                ('task', models.OneToOneField(related_name='resources', to='api.Task')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'workflow', b'Workflow'), (b'step', b'Step')])),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TemplateImport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='WorkflowInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
                ('channel', models.CharField(max_length=255)),
                ('hint', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkflowMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='WorkflowOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')])),
                ('channel', models.CharField(max_length=255)),
            ],
            bases=(models.Model, api.models.base._ModelNameMixin, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='BooleanDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.NullBooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('filename', models.CharField(max_length=1024)),
                ('md5', models.CharField(max_length=255)),
                ('note', models.TextField(max_length=10000, null=True)),
                ('source_url', models.TextField(max_length=1000, null=True)),
                ('source_type', models.CharField(max_length=255, choices=[(b'imported', b'Imported'), (b'result', b'Result'), (b'log', b'Log')])),
                ('file_resource', models.ForeignKey(to='api.FileResource', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='FloatDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.FloatField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='IntegerDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.IntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='RequestedDockerEnvironment',
            fields=[
                ('requestedenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.RequestedEnvironment')),
                ('docker_image', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.requestedenvironment',),
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('template_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.Template')),
                ('command', models.TextField()),
                ('interpreter', models.CharField(default=b'/bin/bash', max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.template',),
        ),
        migrations.CreateModel(
            name='StringDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.TextField(max_length=10000, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='TaskDockerEnvironment',
            fields=[
                ('taskenvironment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.TaskEnvironment')),
                ('docker_image', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.taskenvironment',),
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('template_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='api.Template')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.template',),
        ),
        migrations.AddField(
            model_name='workflowmembership',
            name='child_template',
            field=models.ForeignKey(related_name='parents', to='api.Template', null=True),
        ),
        migrations.AddField(
            model_name='templateimport',
            name='template',
            field=models.OneToOneField(related_name='template_import', to='api.Template'),
        ),
        migrations.AddField(
            model_name='taskoutput',
            name='data_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='taskoutput',
            name='task',
            field=models.ForeignKey(related_name='outputs', to='api.Task'),
        ),
        migrations.AddField(
            model_name='taskinput',
            name='data_object',
            field=models.ForeignKey(to='api.DataObject', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='taskinput',
            name='task',
            field=models.ForeignKey(related_name='inputs', to='api.Task'),
        ),
        migrations.AddField(
            model_name='taskenvironment',
            name='task',
            field=models.OneToOneField(related_name='environment', to='api.Task'),
        ),
        migrations.AddField(
            model_name='taskattemptoutput',
            name='data_object',
            field=models.OneToOneField(related_name='task_attempt_output', null=True, on_delete=django.db.models.deletion.PROTECT, to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskattemptoutput',
            name='task_attempt',
            field=models.ForeignKey(related_name='outputs', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='taskattemptoutput',
            name='task_output',
            field=models.ForeignKey(related_name='task_attempt_outputs', on_delete=django.db.models.deletion.PROTECT, to='api.TaskOutput'),
        ),
        migrations.AddField(
            model_name='taskattemptlogfile',
            name='file',
            field=models.OneToOneField(related_name='task_attempt_log_file', null=True, on_delete=django.db.models.deletion.PROTECT, to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskattemptlogfile',
            name='task_attempt',
            field=models.ForeignKey(related_name='log_files', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='fixedworkflowinput',
            name='data_object',
            field=models.ForeignKey(to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='fixedstepinput',
            name='data_object',
            field=models.ForeignKey(to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='datanode',
            name='data_object',
            field=models.ForeignKey(related_name='data_nodes', to='api.DataObject', null=True),
        ),
        migrations.AddField(
            model_name='datanode',
            name='parent',
            field=models.ForeignKey(related_name='children', to='api.DataNode', null=True),
        ),
        migrations.AddField(
            model_name='arraymembership',
            name='array',
            field=models.ForeignKey(related_name='array_members', to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='arraymembership',
            name='item',
            field=models.ForeignKey(related_name='in_arrays', to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='workflowoutput',
            name='workflow',
            field=models.ForeignKey(related_name='outputs', to='api.Workflow'),
        ),
        migrations.AddField(
            model_name='workflowmembership',
            name='parent_template',
            field=models.ForeignKey(related_name='children', to='api.Workflow'),
        ),
        migrations.AddField(
            model_name='workflowinput',
            name='workflow',
            field=models.ForeignKey(related_name='inputs', to='api.Workflow'),
        ),
        migrations.AddField(
            model_name='stepoutput',
            name='step',
            field=models.ForeignKey(related_name='outputs', to='api.Step'),
        ),
        migrations.AddField(
            model_name='stepinput',
            name='step',
            field=models.ForeignKey(related_name='inputs', to='api.Step'),
        ),
        migrations.AddField(
            model_name='requestedresourceset',
            name='step',
            field=models.OneToOneField(related_name='resources', to='api.Step'),
        ),
        migrations.AddField(
            model_name='requestedenvironment',
            name='step',
            field=models.OneToOneField(related_name='environment', to='api.Step'),
        ),
        migrations.AddField(
            model_name='fixedworkflowinput',
            name='workflow',
            field=models.ForeignKey(related_name='fixed_inputs', to='api.Workflow'),
        ),
        migrations.AddField(
            model_name='fixedstepinput',
            name='step',
            field=models.ForeignKey(related_name='fixed_inputs', to='api.Step'),
        ),
    ]
