import json
import collections
import string
from copy import copy
from apps.controls.helpers import objtools

class Linker(object):

    """
    User input may have object definitions separate from the main data
    tree. Objects are identified by a string value placeholder on the tree
    that corresponds to an "id" value in the object definition.
    This class replaces links with their objects to build the tree.

    Any list with a plural noun as its key defined at root level
    may serve as a match for corresponding objects on the tree,
    where the key is a singular with an "id" as the object, or
    where the key is a plural with a list of id's as the object.
    """

    _to_plural = {
        'session': 'sessions',
        'step_resource_set': 'step_resource_sets',
        'session_resource_set': 'session_resource_sets',
        'application': 'applications',
        'remote_file_location': 'remote_file_locations',
        'file': 'files',
        'step': 'steps'
    }
    _resource_types_singular = _to_plural.keys()
    _resource_types_plural = _to_plural.values()

    _special_key_map_to_resource_type = {
        "save_to": "remote_file_location",
        "import_from": "remote_file_location",
    }
    _special_keys = _special_key_map_to_resource_type.keys()

    def resolve_links_in_json(self, data_json):
        data_obj = json.loads(
            data_json, 
            object_pairs_hook=collections.OrderedDict
        )
        return self.resolve_links(data_obj)

    def resolve_links(self, obj):
        self.root = obj
        self._resolve_links_in_object(self.root)
        self._cleanup(self.root)
        return self.root

    def _resolve_links_in_object(self, obj):
        # Main recursive loop
        if objtools.is_list(obj):
            self._branch_from_list(obj)
        elif objtools.is_dict(obj):
            self._resolve_links_in_dict(obj)
            self._branch_from_list(obj.values())
        else:
            pass

    def _branch_from_list(self, objlist):
        for obj in objlist:
            self._resolve_links_in_object(obj)

    def _resolve_links_in_dict(self, obj):
        for key in obj.keys():
            if key in self._special_keys:
                self._resolve_link_for_special_key(key, obj)
            else:
                self._resolve_link_for_standard_key(key, obj)

    def _resolve_link_for_special_key(self, key, obj):
        resource_type = self._special_key_map_to_resource_type[key]
        # e.g. under {"save_to": ["step1id", "step2id"]}, we will match the ids against
        # resources of type "remote_file_location"
        self._resolve_link(key, obj, resource_type)

    def _resolve_link_for_standard_key(self, key ,obj):
        # e.g. under {"steps": ["step1id", "step2id"]}, we will match the ids against
        # resources of type "step"
        resource_type = key
        self._resolve_link(key, obj, resource_type)

    def _resolve_link(self, key, obj, resource_type):
        if resource_type in self._resource_types_singular:
            self._resolve_link_for_scalar(obj, key, resource_type)
        elif resource_type in self._resource_types_plural:
            self._resolve_links_for_array(obj, key, resource_type)

    def _resolve_link_for_scalar(self, obj, key, resource_type_singular):
        resource_id = obj[key]
        resource_type_plural = self._to_plural[resource_type_singular]
        resource_list = self.root.get(resource_type_plural, [])
        self._match_and_copy_from_resource_list(resource_id, resource_list, obj, key)

    def _resolve_links_for_array(self, obj, key, resource_name_plural):
        resource_list = self.root.get(resource_name_plural, [])
        list_of_resource_ids = self._get_if_list(obj, key)
        for index in range(len(list_of_resource_ids)):
            resource_id = list_of_resource_ids[index]
            self._match_and_copy_from_resource_list(resource_id, resource_list, list_of_resource_ids, index)

    def _match_and_copy_from_resource_list(self, resource_id, resource_list, obj, key):
        # obj can be either a list or a dict
        for resource in resource_list:
            if resource_id == resource.get('id'):
                obj[key] = copy(resource)
                break

    def _get_if_list(self, obj, key):
        if objtools.is_list(obj[key]):
            return obj[key]
        else:
            return []

    def _cleanup(self, obj):
        for item in self._resource_types_plural:
            obj.pop(item, None)
