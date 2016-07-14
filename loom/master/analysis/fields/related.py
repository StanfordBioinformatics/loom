from __future__ import unicode_literals

import django
from django.db.models.fields import related
from django.utils import six


"""Modify ManyToManyField to remove relationship uniqueness constraint,
such that multiple relationships can exist between the same two objects.
"""

RECURSIVE_RELATIONSHIP_CONSTANT = related.RECURSIVE_RELATIONSHIP_CONSTANT
add_lazy_relation = related.add_lazy_relation

# This is an altered copy of
# django.db.models.fields.related.create_many_to_many_model
#
def _create_many_to_many_intermediary_model(field, klass):
    from django.db import models
    managed = True
    if isinstance(field.rel.to, six.string_types) and field.rel.to != RECURSIVE_RELATIONSHIP_CONSTANT:
        to_model = field.rel.to
        to = to_model.split('.')[-1]

        def set_managed(field, model, cls):
            field.rel.through._meta.managed = model._meta.managed or cls._meta.managed
        add_lazy_relation(klass, field, to_model, set_managed)
    elif isinstance(field.rel.to, six.string_types):
        to = klass._meta.object_name
        to_model = klass
        managed = klass._meta.managed
    else:
        to = field.rel.to._meta.object_name
        to_model = field.rel.to
        managed = klass._meta.managed or to_model._meta.managed
    name = '%s_%s' % (klass._meta.object_name, field.name)
    if field.rel.to == RECURSIVE_RELATIONSHIP_CONSTANT or to == klass._meta.object_name:
        from_ = 'from_%s' % to.lower()
        to = 'to_%s' % to.lower()
    else:
        from_ = klass._meta.model_name
        to = to.lower()

    meta = type(str('Meta'), (object,), {
        'db_table': field._get_m2m_db_table(klass._meta),
        'managed': managed,
        'auto_created': klass,
        'app_label': klass._meta.app_label,
        'db_tablespace': klass._meta.db_tablespace,
        #
        # This is the only change from standard ManyToMany. We remove
        # the constraint a relationship has to be unique
        #
        # 'unique_together': (from_, to),
        #
        'verbose_name': '%(from)s-%(to)s relationship' % {'from': from_, 'to': to},
	'verbose_name_plural': '%(from)s-%(to)s relationships' % {'from': from_, 'to': to},
        'apps': field.model._meta.apps,
    })
    # Construct and return the new class.                                                                                                                                            
    return type(str(name), (models.Model,), {
        'Meta': meta,
        '__module__': klass.__module__,
        from_: models.ForeignKey(
            klass,
            related_name='%s+' % name,
            db_tablespace=field.db_tablespace,
            db_constraint=field.rel.db_constraint,
        ),
        to: models.ForeignKey(
            to_model,
            related_name='%s+' % name,
            db_tablespace=field.db_tablespace,
            db_constraint=field.rel.db_constraint,
        )
    })

related.create_many_to_many_intermediary_model = _create_many_to_many_intermediary_model

DuplicateManyToManyField = django.db.models.fields.related.ManyToManyField
