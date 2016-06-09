import re
import uuid

from analysis.exceptions import *
from universalmodels.models import ImmutableModel, InstanceModel


class _ModelMixin(object):
    """This class provides common functions for models,
    including rendering model names for URLs and user messages,
    and query functions for retrieving objects
    """

    _class_name = None
    _class_name_plural = None

    # Used for CamelCase to underscore conversions
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    # To override
    NAME_FIELD = None

    def get_name_and_id(self):
        """Render object ID as {name}@{uuid_or_hash}
        """
        return '%s@%s' % (self.get_name(), self.get_id())

    def get_name(self):
        """Return the name value who's location is given by NAME_FIELD, where
        NAME_FIELD of the form {field1}[__{field2}[__{field3}...]]
        """
        if self.NAME_FIELD is None:
            return ''

        value = self
        for name_part in self.NAME_FIELD.split('__'):
            value = getattr(value, name_part)
        return value

    @classmethod
    def get_class_name(cls, plural=False, hyphen=False):
        if plural:
            name = cls._get_plural_name()
        else:
            name = cls._get_singular_name()
        if hyphen:
            name = name.replace('_','-')
        return name

    @classmethod
    def _get_singular_name(cls):
        if cls._class_name is not None:
            return cls._class_name
        else:
            return cls._camel_to_underscore(cls.__name__)

    @classmethod
    def _get_plural_name(cls):
        if cls._class_name_plural is not None:
            return cls._class_name_plural
        else:
            return cls._pluralize(cls._get_singular_name())

    @classmethod
    def _pluralize(cls, text):
        if text.endswith(('s', 'x')):
            return text + 'es'
        else:
            return text + 's'

    @classmethod
    def _camel_to_underscore(cls, text):
        s1 = cls.first_cap_re.sub(r'\1_\2', text)
        return cls.all_cap_re.sub(r'\1_\2', s1).lower()

    @classmethod
    def get_by_abbreviated_id(cls, _id):
        """Find objects that match the given ID, and allow ID to be truncated
        """
        if not _id:
            raise InvalidIdError('Invalid query, no ID was found')
        return cls.objects.filter(_id__startswith=_id)

    @classmethod
    def get_by_name(cls, name):
        """Returns a queryset of models matching the given name.
        Searches for name at cls.NAME_FIELD of the form 
        {field1}[__{field2}[__{field3}...]]
        """
        if cls.NAME_FIELD is None:
            return cls.objects.none()
        kwargs = {cls.NAME_FIELD: name}
        return cls.objects.filter(**kwargs)

    @classmethod
    def get_by_name_and_full_id(cls, query_string):
        """Find objects that match the given ID, and allow ID to be truncated.
        No truncation allowed.
        """
        name, id, name_or_id = cls._parse_query_string(query_string)
        models = cls.get_by_name(name)
        return models.filter(_id=id)

    @classmethod
    def get_by_name_and_abbreviated_id(cls, query_string):
        """Find objects that match the given {name}@{ID}, where ID may be truncated
        """
        name, id, name_or_id = cls._parse_query_string(query_string)
        models = cls.get_by_name(name)
        return models.filter(_id__startswith=id)
        
    @classmethod
    def get_by_name_or_id(cls, query_string):
        """Find objects that match the identifier of form {name}@{ID}, {name}, {ID}, or @{ID}, 
        where ID may be truncated
        """
        if not cls._is_query_string_valid(query_string):
            return cls.objects.none()
        name, id, name_or_id = cls._parse_query_string(query_string)
        if id and not name:
            try:
                return cls.get_by_abbreviated_id(id)
            except IdTooShortError:
                return cls.objects.none()
        elif name and not id:
            return cls.get_by_name(name)
        elif name and id:
            return cls.get_by_name_and_abbreviated_id(query_string)
        elif name_or_id:
            models1 = cls.get_by_name(name_or_id)
            try:
                models2 = cls.get_by_abbreviated_id(name_or_id)
            except IdTooShortError:
                models2 = cls.objects.none()
            return models1 | models2
        else:
            return cls.objects.none()

    @classmethod
    def _is_query_string_valid(cls, query_string):
        """Matches queries of the form ID, name, name@ID, or @ID.
        """
        match = re.match(r'(^[a-zA-Z0-9_/-/.]*(@[a-fA-F0-9]+)?$)|(^@?[a-fA-F0-9]+$)', query_string)
        return bool(match)

    @classmethod
    def _parse_query_string(cls, query_string):
        if '@' not in query_string:
            name = ''
            id = ''
            name_or_id = query_string
        else:
            (name, id) = query_string.split('@')
            name_or_id = ''
        return (name, id, name_or_id)


class AnalysisAppInstanceModel(InstanceModel, _ModelMixin):

    def __unicode__(self):
        return uuid.UUID(str(self._id)).hex

    class Meta:
        abstract = True
        app_label = 'analysis'


class AnalysisAppImmutableModel(ImmutableModel, _ModelMixin):

    def __unicode__(self):
        return self._id

    class Meta:
        abstract = True
        app_label = 'analysis'
