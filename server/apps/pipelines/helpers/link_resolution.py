import json
import collections
import string
from copy import copy

class LinkResolutionHelper(object):

    """
    User input may have object definitions separate from the data
    tree. Objects are identified by an "id" placeholder on the tree.
    This class builds the full tree based on links to object
    definitions, and returns just the tree.

    Any list with a plural noun as its key defined at root level
    may serve as a match for corresponding objects on the tree,
    where the key is a singular with an "id" as the object, or
    where the key is a plural with a list of id's as the object.
    """

    resources = {
        'session': 'sessions',
        'step_resource_set': 'step_resource_sets',
        'session_resource_set': 'session_resource_sets',
        'application': 'applications',
        'remote_file_location': 'remote_file_locations',
        'file': 'files',
        'step': 'steps'
    }
    resources_as_singular = resources.keys()
    resources_as_plural = resources.values()

    special_key_map_to_resource = {
        "save_to": "remote_file_location",
        "import_from": "remote_file_location",
    }
    special_keys = special_key_map_to_resource.keys()


    def resolve_links_in_json(self, data_json):
        data_obj = json.loads(
            data_json, 
            object_pairs_hook=collections.OrderedDict
        )
        return self.resolve_links(data_obj)

    def resolve_links(self, obj):
        # Initialize by remembering the root node
        self.root = obj
        self._resolve_links_in_object(obj)
        self._cleanup(obj)
        return obj

    def _resolve_links_in_object(self, obj):
        # Main recursive loop
        if self._is_list(obj):
            self._branch_from_list(obj)
        elif self._is_dict(obj):
            self._resolve_links_in_dict(obj)
            self._branch_from_list(obj.values())
        else:
            pass

    def _branch_from_list(self, objlist):
        for obj in objlist:
            self._resolve_links_in_object(obj)

    def _resolve_links_in_dict(self, obj):
        """
        Algorithm:
         For each dict key anywhere in obj:
          if key in resources.keys (singluar) and 
             value is the id of an object in the list at root[plural(key)]
               replace id value with object
          elif key in resources.values (plural) and value is a list
            for each item
              if value is the id of an object in the list at root[plural(key)]
                replace id value with object
        """
        for obj_key in obj.keys():
            if obj_key in self.special_keys:
                resource_name = self.special_key_map_to_resource[obj_key]
            else:
                resource_name = obj_key

            if resource_name in self.resources_as_singular:
                self._check_for_scalar(obj, obj_key, resource_name)
            elif resource_name in self.resources_as_plural:
                self._check_for_array(obj, obj_key, resource_name)

    def _check_for_scalar(self, obj, obj_key, resource_name_singular):
        might_be_an_id = obj[obj_key]
        resource_name_plural = self.resources[resource_name_singular]
        resource_definitions = self.root.get(resource_name_plural, None)
        if resource_definitions is None:
            return
        for resource in resource_definitions:
            if resource.get('id') == might_be_an_id:
                obj[obj_key] = copy(resource)
                break

    def _check_for_array(self, obj, obj_key, resource_name_plural):
        resource_definitions = self.root.get(resource_name_plural, None)
        if resource_definitions is None:
            return
        might_be_a_list_of_ids = obj[obj_key]
        if not self._is_list(might_be_a_list_of_ids):
            return
        for i in range(len(might_be_a_list_of_ids)):
            might_be_an_id = might_be_a_list_of_ids[i]
            for resource in resource_definitions:
                if resource.get('id') == might_be_an_id:
                    might_be_a_list_of_ids[i] = copy(resource)
                    break

    def _is_string(self, obj):
        return isinstance(obj, basestring)

    def _is_list(self, obj):
        return isinstance(obj, (list, tuple))

    def _is_dict(self, obj):
        return hasattr(obj, 'keys') and hasattr(obj, 'values')

    def _cleanup(self, obj):
        for item in self.resources_as_plural:
            obj.pop(item, None)
