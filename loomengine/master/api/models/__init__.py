import jinja2
import uuid

def uuidstr():
    return str(uuid.uuid4())

def render_from_template(raw_text, context):
    if not raw_text:
	return ''
    loader = jinja2.DictLoader({'template': raw_text})
    env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
    template = env.get_template('template')
    return template.render(**context)

def render_string_or_list(value, context):
    if isinstance(value, list):
	return [render_from_template(member, context)
		for member in value]
    else:
        return render_from_template(value, context)

class ArrayInputContext(object):
    """This class is used with jinja templates to make the 
    default representation of an array a space-delimited list.
    """

    def __init__(self, items, type):
        if type == 'file':
            self.items = self._rename_duplicates(items)
        else:
            self.items = items

    def _rename_duplicates(self, filenames):

        # Identify filenames that are unique
        seen = set()
        duplicates = set()
        for filename in filenames:
            if filename in seen:
                duplicates.add(filename)
            seen.add(filename)

        new_filenames = []
        filename_counts = {}
        for filename in filenames:
            if filename in duplicates:
                counter = filename_counts.setdefault(filename, 0)
                filename_counts[filename] += 1
                filename = self._add_counter_suffix(filename, counter)
            new_filenames.append(filename)
        return new_filenames

    def _add_counter_suffix(self, filename, count):
        # Add suffix while preserving file extension:
        #   myfile -> myfile.__1__
        #   myfile.txt --> myfile__1__.txt
        #   my.file.txt --> my.file__1__.txt
        parts = filename.split('.')
        assert len(parts) > 0, 'missing filename'
        if len(parts) == 1:
            return parts[0] + '__%s__' % count
        else:
            return '.'.join(parts[0:len(parts)-1]) + '__%s__.' % count + parts[-1]

    def __iter__(self):
        return self.items.__iter__()

    def __getitem__(self, i):
        return self.items[i]

    def __str__(self):
        return ' '.join([str(item) for item in self.items])

from .data_objects import *
from .data_nodes import *
from .runs import *
from .tags import *
from .task_attempts import *
from .tasks import *
from .templates import *
