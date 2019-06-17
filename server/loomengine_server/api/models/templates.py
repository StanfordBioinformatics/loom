from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import jsonfield

from . import flatten_nodes, copy_prefetch
from .base import BaseModel
from .data_channels import DataChannel
from .data_nodes import DataNode
from api import get_setting
from api.models import uuidstr
from api.models import validators


"""
A Template is the pattern for a Run. Has defined inputs and outputs,
but the data designated for each input is only designated at runtime.

A Template may define a default value for each input, but this can
be overridden at runtime.

Templates may be nested to arbitrary depth. Only the leaf nodes
represent actual analysis Runs. Both leaf and branch nodes are
represented by the Template class.
"""


class Template(BaseModel):

    NAME_FIELD = 'name'
    HASH_FIELD = 'md5'
    ID_FIELD = 'uuid'
    TAG_FIELD = 'tags__tag'

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    name = models.CharField(max_length=255,
                            validators=[validators.TemplateValidator.validate_name])
    md5 = models.CharField(null=True, blank=True,
                           max_length=32, validators=[validators.validate_md5])
    is_leaf = models.BooleanField()
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    timeout_hours = models.FloatField(null=True, blank=True)
    command = models.TextField(blank=True)
    interpreter = models.CharField(max_length=1024, blank=True)
    environment = jsonfield.JSONField(
        blank=True,
        validators=[validators.validate_environment])
    resources = jsonfield.JSONField(
        blank=True,
        validators=[validators.validate_resources])
    import_comments = models.TextField(blank=True)
    imported_from_url = models.TextField(
        blank=True,
	validators=[validators.validate_url])
    imported = models.BooleanField(default=False)
    steps = models.ManyToManyField(
        'Template',
        through='TemplateMembership',
        through_fields=('parent_template', 'child_template'),
        related_name='parents')
    outputs = jsonfield.JSONField(
        validators=[validators.TemplateValidator.validate_outputs],
        blank=True
    )
    raw_data = jsonfield.JSONField(blank=True)

    def get_name_and_id(self):
        return "%s@%s" % (self.name, self.id)

    def get_input(self, channel):
        inputs = self.inputs.filter(channel=channel)
        if inputs.count() == 0:
            raise ObjectDoesNotExist('No input with channel "%s"' % channel)
        assert inputs.count() == 1, \
            'Found %s inputs for channel %s' % (inputs.count(), channel)
        return inputs.first()

    def get_output(self, channel):
        outputs = filter(lambda o: o.get('channel')==channel,
                         self.outputs)
        assert outputs.count() == 1, \
            'Found %s outputs for channel %s' %(outputs.count(), channel)
        return outputs.first()

    def add_step(self, step):
        TemplateMembership.add_step_to_workflow(step, self)

    def add_steps(self, step_list):
        for step in step_list:
            self.add_step(step)


    @classmethod
    def get_dependencies(cls, uuid):
        DEPENDENCY_LIMIT = 10
        truncated = False
        runs = set()
        templates = set()

        template = cls.objects.filter(uuid=uuid)\
                              .prefetch_related('parent_templates__parent_template')\
                              .prefetch_related('runs')
        if template.count() < 1:
            raise cls.DoesNotExist
        
        for run in template.first().runs.all():
            if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
               and run not in runs:
                truncated = True
                break
            runs.add(run)
        for template in template.first().parents.all():
            if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
               and run not in runs:
                truncated = True
                break
            templates.add(template)

        return {'runs': runs,
                'templates': templates,
                'truncated': truncated}

    def delete(self):
        from api.models.data_nodes import DataNode
        if self.parents.count() != 0:
            raise models.ProtectedError(
                'Cannot delete template "@%s" because it is contained by '
                '1 or more other templates' % self.uuid, 
                [template for template in self.parents.all()])
        nodes_to_delete = set()
	queryset = DataNode.objects.filter(
            templateinput__template__uuid=self.uuid)
        for item in queryset.all():
            nodes_to_delete.add(item)
        super(Template, self).delete()
        for item in nodes_to_delete:
            try:
                item.delete()
            except models.ProtectedError:
                pass

    def prefetch(self):
        if not hasattr(self, '_prefetched_objects_cache'):
            self.prefetch_list([self,])

    @classmethod
    def prefetch_list(cls, instances):
        queryset = Template\
                   .objects\
                   .filter(uuid__in=[i.uuid for i in instances])
        MAXIMUM_TREE_DEPTH = get_setting('MAXIMUM_TREE_DEPTH')
        # Prefetch 'children', 'children__children', etc. up to max depth
        # This incurs 1 query per level up to actual depth.
        # No extra queries incurred if we go too deep.)
        for i in range(1, MAXIMUM_TREE_DEPTH+1):
            queryset = queryset.prefetch_related('__'.join(['steps']*i))
        # Transfer prefetched steps to original instances
        queried_templates_1 = [template for template in queryset]
        copy_prefetch(queried_templates_1, instances)
        # Flatten tree so we can simultaneously prefetch related models on all nodes
        node_list = []
        for instance in instances:
            node_list.extend(flatten_nodes(instance, 'steps'))
        queryset = Template.objects.filter(uuid__in=[n.uuid for n in node_list])\
            .prefetch_related('inputs')\
            .prefetch_related('inputs__data_node')
        # Transfer prefetched data to child nodes on original instances
        queried_templates_2 = [template for template in queryset]
        copy_prefetch(queried_templates_2, instances, child_field='steps')
        # Prefetch all data nodes
        data_nodes = []
	for instance in instances:
            instance._get_data_nodes(data_nodes=data_nodes)
	DataNode.prefetch_list(data_nodes)

    def _get_data_nodes(self, data_nodes=None):
        if data_nodes is None:
            data_nodes = []
        for input in self.inputs.all():
            if input.data_node:
                data_nodes.append(input.data_node)
        return data_nodes

    @classmethod
    def _prefetch_for_filter(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()
        return queryset.prefetch_related('tags')

class TemplateInput(DataChannel):

    template = models.ForeignKey(
        'Template',
        related_name='inputs',
        on_delete=models.CASCADE)
    hint = models.CharField(max_length=1000, blank=True)
    mode = models.CharField(max_length=255, blank=True)
    group = models.IntegerField(null=True, blank=True)
    as_channel = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'api'

    @property
    def data(self):
        # Dummy attribute required by serializer
        return


class TemplateMembership(BaseModel):

    parent_template = models.ForeignKey('Template', related_name='child_templates',
                                        on_delete=models.CASCADE)
    child_template = models.ForeignKey('Template', related_name='parent_templates', 
                                       null=True, blank=True,
                                       on_delete=models.CASCADE)

    @classmethod
    def add_step_to_workflow(cls, step, parent):
            template_membership = TemplateMembership(
                parent_template=parent,
                child_template=step)
            template_membership.full_clean()
            template_membership.save()
