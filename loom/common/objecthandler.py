import json
import requests
from loom.common.exceptions import *

class ObjectHandler(object):
    """ObjectHandler provides functions to create and work with objects in the 
    Loom database via the HTTP API
    """

    def __init__(self, master_url):
        self.api_root_url = master_url + '/api/'

    def _post(self, data, relative_url):
        url = self.api_root_url + relative_url
        return self._make_request_to_server(lambda: requests.post(url, data=json.dumps(data)))

    def _post_object(self, object_data, relative_url):
        return self._post(object_data, relative_url)['object']

    def _get(self, relative_url):
        url = self.api_root_url + relative_url
        return self._make_request_to_server(lambda: requests.get(url))

    def _make_request_to_server(self, query_function):
        """Verifies server connection and handles response errors
        for either get or post requests
        """
        try:
            response = query_function()
        except requests.exceptions.ConnectionError as e:
            raise ServerConnectionError("No response from server.\n%s" % (url, e))
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise BadResponseError("%s\n%s" % (e.message, response.text))
        return response.json()
    
            
    def post_data_object_array(self, data_object_array):
        return self._post_object(
            data_object_array,
            'data_object_arrays/')

    def post_file_data_object(self, file_data_object):
        return self._post_object(
            file_data_object,
            'file_data_objects/') 
    
    def post_file_storage_location(self, file_storage_location):
        return self._post_object(
            file_storage_location,
            'file_storage_locations/')

    def post_data_source_record(self, data_source_record):
        return self._post_object(
            data_source_record,
            'data_source_records/'
        )

    def get_server_time(self):
        return self._get('servertime/')['time']
