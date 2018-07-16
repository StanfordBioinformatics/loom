import django.db.utils
from django.db import models, transaction
import re

from api.exceptions import ConcurrentModificationError, SaveRetriesExceededError


"""BaseModel is an abstract class that adds the following to 
models that extend this class:
- Protection against data overwrite by concurrent editing
- Querying by string identifies consisting of name, ID, and/or hash
"""


class FilterHelper(object):
    """
    Many object types are queryable by a user input string that gives name,
    uuid, and/or hash value,
    e.g. myfile.dat, myfile.data@1ca14b82-df57-437f-b296-dfd6118132ab,
    or myfile.dat$3c0e6b886ea83d2895fd64fd6619a99f
    This class parses those query strings and searches for matches.
    """

    def __init__(self, Model):
        self.Model = Model

    def filter_multiple_by_name_or_id_or_tag_or_hash(
            self, query_strings, queryset=None):
        assert isinstance(query_strings, (list, set))
        query_strings = set(query_strings)
        if len(query_strings) == 0:
            return {}
        results = self.Model.objects.none()
        for query_string in query_strings:
            results = results | self.filter_by_name_or_id_or_tag_or_hash(
                query_string, queryset=queryset)
        return self._sort_by_name_or_id_or_tag_or_hash(
            query_strings, results)

    def _sort_by_name_or_id_or_tag_or_hash(self, query_strings, results):
        models = [r for r in results]
        sorted_results = {}
        for query_string in query_strings:
            name, uuid, tag, hash_value \
                = self._parse_as_name_or_id_or_tag_or_hash(query_string)
            matches = list(filter(
                lambda model: self._does_model_match(
                    model, name=name, uuid=uuid,
                    tag=tag, hash_value=hash_value),
                results))
            sorted_results[query_string] = matches
        return sorted_results

    def filter_multiple_by_name_or_id_or_tag(
            self, query_strings, queryset=None):
        assert isinstance(query_strings, (list, set))
        query_strings = set(query_strings)
        if len(query_strings) == 0:
            return {}
        results = self.Model.objects.none()
        for query_string in query_strings:
            results = results | self.filter_by_name_or_id_or_tag(
                query_string, queryset=queryset)
        return self._sort_by_name_or_id_or_tag(
            query_strings, results)

    def _sort_by_name_or_id_or_tag(self, query_strings, results):
        models = [r for r in results]
        sorted_results = {}
        for query_string in query_strings:
            name, uuid, tag = self._parse_as_name_or_id_or_tag(query_string)
            matches = list(filter(
                lambda model: self._does_model_match(
                    model, name=name, uuid=uuid,
                    tag=tag),
                results))
            sorted_results[query_string] = matches
        return sorted_results

    @classmethod
    def _does_model_match(cls, model, name=None, uuid=None, tag=None, hash_value=None):
        if name and not cls._get_field_value(
                model, model.NAME_FIELD)==name:
            return False
        if uuid and not cls._get_field_value(
                model, model.ID_FIELD).startswith(uuid):
            return False
        if tag and not tag in [t.tag for t in model.tags.all()]:
            return False
        if hash_value and not cls._get_field_value(model, model.HASH_FIELD)==hash_value:
            return False
        return True

    @classmethod
    def _get_field_value(cls, model, field):
        value = model
        for attr in field.split('__'):
            value = getattr(value, attr)
        return value

    def filter_by_name_or_id_or_tag_or_hash(self, query_string, queryset=None):
        assert self.Model.NAME_FIELD, \
            'NAME_FIELD is missing on model %s' % self.Model.__name__
        assert self.Model.HASH_FIELD, \
            'HASH_FIELD is missing on model %s' % self.Model.__name__
        assert self.Model.ID_FIELD, \
            'ID_FIELD is missing on model %s' % self.Model.__name__
        assert self.Model.TAG_FIELD, \
            'TAG_FIELD is missing on model %s' % self.Model.__name__
        
        filter_args = {}
        name, uuid, tag, hash_value = self._parse_as_name_or_id_or_tag_or_hash(
            query_string)
        if name is not None:
            filter_args[self.Model.NAME_FIELD] = name
        if hash_value is not None:
            filter_args[self.Model.HASH_FIELD+'__startswith'] = hash_value
        if uuid is not None:
            filter_args[self.Model.ID_FIELD+'__startswith'] = uuid
        if tag is not None:
            filter_args[self.Model.TAG_FIELD] = tag
        if queryset is None:
            queryset = self.Model.objects.all()
        return queryset.filter(**filter_args)

    def filter_by_name_or_id_or_tag(self, query_string, queryset = None):
        """Find objects that match the identifier of form {name}@{ID}, {name},
        or @{ID}, where ID may be truncated
        """
        assert self.Model.NAME_FIELD, \
            'NAME_FIELD is missing on model %s' % self.Model.__name__
        assert self.Model.ID_FIELD, \
            'ID_FIELD is missing on model %s' % self.Model.__name__
        assert self.Model.TAG_FIELD, \
            'TAG_FIELD is missing on model %s' % self.Model.__name__

        filter_args = {}
        name, uuid, tag = self._parse_as_name_or_id_or_tag(query_string)
        if name is not None:
            filter_args[self.Model.NAME_FIELD] = name
        if uuid is not None:
            filter_args[self.Model.ID_FIELD+'__startswith'] = uuid
        if tag is not None:
            filter_args[self.Model.TAG_FIELD] = tag
        if queryset is None:
            queryset = self.Model.objects.all()
        return queryset.filter(**filter_args)

    def _parse_as_name_or_id_or_tag_or_hash(self, query_string):
        name = None
        uuid = None
        hash_value = None
        tag = None
        # Name comes at the beginning and ends with $, @, :, or end of string
        name_match = re.match('^(?!\$|@|:)(.+?)($|\$|@|:)', query_string)
        if name_match is not None:
            name = name_match.groups()[0]
        # id starts with @ and ends with $ or end of string
        uuid_match = re.match('^.*?@(.*?)($|\$|:)', query_string)
        if uuid_match is not None:
            uuid = uuid_match.groups()[0]
        # tag starts with $ and ends with @ or end of string
        tag_match = re.match('^.*?:(.*?)($|\$|@)', query_string)
        if tag_match is not None:
            tag = tag_match.groups()[0]
        # hash starts with $ and ends with @ or end of string
        hash_match = re.match('^.*?\$(.*?)($|@|:)', query_string)
        if hash_match is not None:
            hash_value = hash_match.groups()[0]
        return name, uuid, tag, hash_value

    def _parse_as_name_or_id_or_tag(self, query_string):
        name, uuid, tag, hash_value = self._parse_as_name_or_id_or_tag_or_hash(
            query_string)
        if hash_value is not None:
            raise Exception('Invalid input "%s". '\
                            'Hash not accepted for models of type "%s"' %
                            (query_string, self.Model.__name__))
        return name, uuid, tag


class _FilterMixin(object):

    NAME_FIELD = None
    HASH_FIELD = None
    ID_FIELD = None

    @classmethod
    def filter_by_name_or_id_or_tag_or_hash(cls, filter_string, queryset=None):
        helper = FilterHelper(cls)
        return helper.filter_by_name_or_id_or_tag_or_hash(
            filter_string, queryset=queryset)

    @classmethod
    def filter_by_name_or_id_or_tag(cls, filter_string):
        helper = FilterHelper(cls)
        return helper.filter_by_name_or_id_or_tag(filter_string)

    @classmethod
    def filter_multiple_by_name_or_id_or_tag_or_hash(
            cls, filter_strings, queryset=None):
        helper = FilterHelper(cls)
        return helper.filter_multiple_by_name_or_id_or_tag_or_hash(
            filter_strings, queryset=queryset)

    @classmethod
    def filter_multiple_by_name_or_id_or_tag(cls, filter_strings):
        helper = FilterHelper(cls)
        return helper.filter_multiple_by_name_or_id_or_tag(filter_strings)

    @classmethod
    def _prefetch_for_filter(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()
        return queryset


class BaseModel(models.Model, _FilterMixin):
    _change = models.IntegerField(default=0)

    class Meta:
        abstract = True
        app_label = 'api'

    def save(self, *args, **kwargs):
        """
        This save method protects against two processesses concurrently modifying
        the same object. Normally the second save would silently overwrite the
        changes from the first. Instead we raise a ConcurrentModificationError.
        """
        cls = self.__class__
        if self.pk:
            rows = cls.objects.filter(
                pk=self.pk, _change=self._change).update(
                _change=self._change + 1)
            if not rows:
                raise ConcurrentModificationError(cls.__name__, self.pk)
            self._change += 1

        count = 0
        max_retries=3
        while True:
            try:
                return super(BaseModel, self).save(*args, **kwargs)
            except django.db.utils.OperationalError:
                if count >= max_retries:
                    raise
                count += 1

    def setattrs_and_save_with_retries(self, assignments, max_retries=5):
        """
        If the object is being edited by other processes,
        save may fail due to concurrent modification.
        This method recovers and retries the edit.

        assignments is a dict of {attribute: value}
        """
        count = 0
        obj=self
        while True:
            for attribute, value in assignments.iteritems():
                setattr(obj, attribute, value)
            try:
                obj.full_clean()
                obj.save()
            except ConcurrentModificationError:
                if  count >= max_retries:
                    raise SaveRetriesExceededError(
                        'Exceeded retries when saving "%s" of id "%s" '\
                        'with assigned values "%s"' %
                        (self.__class__, self.id, assignments))
                count += 1
                obj = self.__class__.objects.get(id=self.id)
                continue
            return obj

    def delete(self, *args, **kwargs):
        """
        This method implements retries for object deletion.
        """
        count = 0
        max_retries=3
        while True:
            try:
                return super(BaseModel, self).delete(*args, **kwargs)
            except django.db.utils.OperationalError:
                if count >= max_retries:
                    raise
                count += 1
