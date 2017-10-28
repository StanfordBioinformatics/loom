import json
import requests
import time
import datetime
import urllib

from .exceptions import *

def disable_insecure_request_warning():
    """Suppress warning about untrusted SSL certificate."""
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Connection(object):
    """Connection provides functions to create and work with objects in the 
    Loom database via the HTTP API
    """

    def __init__(self, master_url, token=None):
        self.api_root_url = master_url + '/api/'
        self.token = token

    # ---- General methods ----

    def _add_token(self, headers):
        if self.token is not None:
            headers['Authorization'] = 'Token %s' % self.token
        return headers

    def _post(self, data, relative_url):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()      
        return self._make_request_to_server(
            lambda: requests.post(
                url,
                data=json.dumps(data),
                headers=self._add_token({'content-type': 'application/json'}),
                verify=False,
            ))

    def _put(self, data, relative_url):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.put(
                url,
                data=json.dumps(data),
                headers=self._add_token({'content-type': 'application/json'}),
                verify=False))

    def _patch(self, data, relative_url):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.patch(
                url,
                data=json.dumps(data),
                headers=self._add_token({'content-type': 'application/json'}),
                verify=False))

    def _get(self, relative_url, raise_for_status=True, params=None):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.get(
                url,
                verify=False, # Don't fail on unrecognized SSL certificate
                params=params,
                headers=self._add_token({})), 
            raise_for_status=raise_for_status)

    def _delete(self, relative_url, raise_for_status=True):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.delete(
                url,
                headers=self._add_token({'content-type': 'application/json'}),
                verify=False,
            ),
            raise_for_status=raise_for_status
        )

    def _make_request_to_server(self, query_function, raise_for_status=True):
        """Verifies server connection and handles response errors
        for either get or post requests
        """
        # Try to connect every {retry_delay_seconds} until {time_limit_seconds} or until
        # the response returns without error.
        start_time = datetime.datetime.now()
        time_limit_seconds = 2
        retry_delay_seconds = 0.2
        while datetime.datetime.now() - start_time < datetime.timedelta(0, time_limit_seconds):
            error = None
            try:
                response = query_function()
                if raise_for_status:
                    response.raise_for_status()
            except requests.exceptions.ConnectionError as e:
                error = ServerConnectionError("No response from server.\n%s" % e.message)
            except:
                print response.text
                raise
            if error:
                time.sleep(retry_delay_seconds)
                continue
            else:
                return response
        raise error

    def _post_object(self, object_data, relative_url):
        return self._post(object_data, relative_url).json()

    def _put_object(self, object_data, relative_url):
        return self._put(object_data, relative_url).json()

    def _patch_object(self, object_data, relative_url):
        return self._patch(object_data, relative_url).json()

    def _delete_object(self, relative_url):
        self._delete(relative_url, raise_for_status=True)

    def _get_object(self, relative_url, params=None):
        # Do not raise_for_status, because we want to check for 404 here
        response = self._get(relative_url, raise_for_status=False, params=params)
        if response.status_code == 404:
            return None
        elif response.status_code == 200:
            return response.json()
        else:
            raise BadResponseError("Status code %s. %s" % (response.status_code, response.text))

    def _get_object_index(self, relative_url, params=None):
        response = self._get(relative_url, params=params)
        return response.json()

    # ---- Post/Put/Get [object_type] methods ----

    def post_data_object(self, data):
        return self._post_object(
            data,
            'data-objects/')

    def get_data_object(self, data_object_id):
        return self._get_object(
            'data-objects/%s/' % data_object_id)

    def update_data_object(self, data_object_id, data_update):
        return self._patch_object(
            data_update,
            'data-objects/%s/' % data_object_id)

    def get_data_object_index_with_limit(
            self, query_string=None, source_type=None,
            labels=None,
            type=None,
            limit=10, offset=0):
        url = 'data-objects/'
        params = {}
        if query_string:
            params['q'] = query_string
        if source_type:
            params['source_type'] = source_type
        if type:
            params['type'] = type
        if labels:
            params['labels'] = ','.join(labels)
        params['limit'] = limit
        params['offset'] = offset
        data = self._get_object_index(url, params=params)
        return data

    def get_data_object_index(
            self, query_string=None, source_type=None,
            labels=None,
            type=None, min=0, max=float('inf')):
        url = 'data-objects/'
        params = {}
        if query_string:
            params['q'] = query_string
        if source_type:
            params['source_type'] = source_type
        if type:
            params['type'] = type
        if labels:
            params['labels'] = ','.join(labels)
        data_objects =  self._get_object_index(url, params=params)
        if len(data_objects) < min:
            raise IdMatchedTooFewDataObjectsError(
                'Found %s DataObjects, expected at least %s' \
                % (len(data_objects), min))
        if len(data_objects) > max:
            raise IdMatchedTooManyDataObjectsError(
                'Found %s DataObjects, expected at most %s' \
                % (len(data_objects), max))
        return data_objects

    def get_data_tag_index(self):
        return self._get_object_index('data-tags/')

    def get_template_tag_index(self):
        return self._get_object_index('template-tags/')

    def get_run_tag_index(self):
        return self._get_object_index('run-tags/')

    def get_data_label_index(self):
        return self._get_object_index('data-labels/')

    def get_template_label_index(self):
        return self._get_object_index('template-labels/')

    def get_run_label_index(self):
        return self._get_object_index('run-labels/')

    def get_data_node(self, data_node_id, expand=False):
        params = {}
        if expand:
            params['expand'] = '1'
        return self._get_object(
            'data-nodes/%s/' % data_node_id, params)

    def get_data_node_index(self):
        return self._get_object_index(
            'data-nodes/'
        )

    def get_file_imports_by_file(self, file_id):
        return self._get_object_index(
            'data-files/' + file_id + '/file-imports/'
        )

    def get_template(self, template_id, summary=False,
                     expand=False):
        params = {}
        if summary:
            params['summary'] = '1'
        if expand:
            params['expand'] = '1'
        return self._get_object(
            'templates/%s/' % template_id, params=params
        )
    
    def get_template_index_with_limit(self, query_string=None, imported=False,
                                 labels=None, limit=10, offset=0):
        url = 'templates/'
        params = {}
        if query_string:
            params['q'] = query_string
        if imported:
            params['imported'] = '1'
        if labels:
            params['labels'] = ','.join(labels)
        params['limit'] = limit
        params['offset'] = offset
        return self._get_object_index(url, params=params)

    def get_template_index(self, query_string='', imported=False,
                           labels=None, min=0, max=float('inf')):
        url = 'templates/'
        params = {}
        if query_string:
            params['q'] = query_string
        if imported:
            params['imported'] = '1'
        if labels:
            params['labels'] = ','.join(labels)
        templates = self._get_object_index(url, params=params)
        if len(templates) < min:
            raise Error('Found %s templates, expected at least %s' %(len(templates), min))
        if len(templates) > max:
            raise Error('Found %s templates, expected at most %s' %(len(templates), max))
        return templates

    def post_template(self, template):
        return self._post_object(
            template,
            'templates/')

    def get_run(self, run_id):
        return self._get_object(
            'runs/%s/' % run_id
        )

    def get_run_index_with_limit(self, query_string=None, parent_only=False,
                                 labels=None, limit=10, offset=0):
        url = 'runs/'
        params = {}
        if query_string:
            params['q'] = query_string
        if parent_only:
            params['parent_only'] = '1'
        if labels:
            params['labels'] = ','.join(labels)
        params['limit'] = limit
        params['offset'] = offset
        return self._get_object_index(url, params=params)

    def get_run_index(self, query_string=None, parent_only=False,
                      labels=None,
                      min=0, max=float('inf')):
        url = 'runs/'
        params = {}
        if query_string:
            params['q'] = query_string
        if parent_only:
            params['parent_only'] = '1'
        if labels:
            params['labels'] = ','.join(labels)
        runs = self._get_object_index(url, params=params)
        if len(runs) < min:
            raise Error('Found %s template runs, expected at least %s' %(len(runs), min))
        if len(runs) > max:
            raise Error('Found %s template runs, expected at most %s' %(len(runs), max))
        return runs

    def post_run(self, run):
        return self._post_object(
            run,
            'runs/')

    def post_task(self, task):
        return self._post_object(
            task,
            'tasks/')

    def get_task_attempt(self, task_attempt_id):
        return self._get_object(
            'task-attempts/%s/' % task_attempt_id
        )

    def update_task_attempt(self, task_attempt_id, task_attempt_update):
        return self._patch_object(
            task_attempt_update,
            'task-attempts/%s/' % task_attempt_id)

    def get_task_attempt_output(self, task_attempt_output_id):
        return self._get_object(
            'outputs/%s/' % task_attempt_output_id
        )

    def update_task_attempt_output(self, task_attempt_output_id,
                                   task_attempt_output_update):
        return self._patch_object(
            task_attempt_output_update,
            'outputs/%s/' % task_attempt_output_id)

    def post_task_attempt_log_file(self, task_attempt_id, task_attempt_log_file):
        return self._post_object(
            task_attempt_log_file,
            'task-attempts/%s/log-files/' % task_attempt_id
        )
    
    def post_task_attempt_log_file_data_object(
            self, task_attempt_log_file_id, data_object):
        return self._post_object(
            data_object,
            'log-files/%s/data-object/' % task_attempt_log_file_id
        )

    def post_task_attempt_event(self, task_attempt_id, task_attempt_event):
        return self._post_object(
            task_attempt_event,
            'task-attempts/%s/events/' % task_attempt_id
        )

    def post_task_attempt_system_error(self, task_attempt_id):
        return self._post_object(
            {},
            'task-attempts/%s/system-error/' % task_attempt_id)

    def post_task_attempt_analysis_error(self, task_attempt_id):
        return self._post_object(
            {},
            'task-attempts/%s/analysis-error/' % task_attempt_id)

    def post_task_attempt_finish(self, task_attempt_id):
        return self._post_object(
            {},
            'task-attempts/%s/finish/' % task_attempt_id)

    def post_abstract_file_import(self, file_import):
        return self._post_object(
            file_import,
            'abstract-file-imports/')

    def update_abstract_file_import(self, file_import_id, file_import_update):
        return self._patch_object(
            file_import_update,
            'abstract-file-imports/%s/' % file_import_id)

    def post_run_tag(self, run_id, data):
        return self._post_object(
            data,
            'runs/%s/add-tag/' % run_id)

    def list_run_tags(self, run_id):
        return self._get_object(
            'runs/%s/tags/' % run_id)

    def remove_run_tag(self, run_id, data):
        return self._post_object(
            data,
            'runs/%s/remove-tag/' % run_id)

    def post_data_tag(self, data_object_id, data):
        return self._post_object(
            data,
            'data-objects/%s/add-tag/' % data_object_id)

    def list_data_tags(self, data_object_id):
        return self._get_object(
            'data-objects/%s/tags/' % data_object_id)

    def remove_data_tag(self, data_object_id, data):
        return self._post_object(
            data,
            'data-objects/%s/remove-tag/' % data_object_id)

    def post_template_tag(self, template_id, data):
        return self._post_object(
            data,
            'templates/%s/add-tag/' % template_id)

    def list_template_tags(self, template_id):
        return self._get_object(
            'templates/%s/tags/' % template_id)

    def remove_template_tag(self, template_id, data):
        return self._post_object(
            data,
            'templates/%s/remove-tag/' % template_id)

    def post_run_label(self, run_id, data):
        return self._post_object(
            data,
            'runs/%s/add-label/' % run_id)

    def list_run_labels(self, run_id):
        return self._get_object(
            'runs/%s/labels/' % run_id)

    def remove_run_label(self, run_id, data):
        return self._post_object(
            data,
            'runs/%s/remove-label/' % run_id)

    def post_data_label(self, data_object_id, data):
        return self._post_object(
            data,
            'data-objects/%s/add-label/' % data_object_id)

    def list_data_labels(self, data_id):
        return self._get_object(
            'data-objects/%s/labels/' % data_id)

    def remove_data_label(self, data_id, data):
        return self._post_object(
            data,
            'data-objects/%s/remove-label/' % data_id)

    def post_template_label(self, template_id, data):
        return self._post_object(
            data,
            'templates/%s/add-label/' % template_id)

    def list_template_labels(self, template_id):
        return self._get_object(
            'templates/%s/labels/' % template_id)

    def remove_template_label(self, template_id, data):
        return self._post_object(
            data,
            'templates/%s/remove-label/' % template_id)

    def get_info(self):
        try:
            response = self._get('info/')
        except ServerConnectionError:
            return None
        try:
            info = response.json()
        except ValueError:
            info = None
        return info

    def get_version(self):
        info = self.get_info()
        if not info:
            return None
        return info.get('version')

    def get_task_attempt_settings(self, attempt_id):
        return self._get_object(
            'task-attempts/%s/settings/' % attempt_id
        )

    def get_filemanager_settings(self):
        return self._get_object(
            'filemanager-settings/'
        )

    def create_token(self, username=None, password=None):
        response = requests.post(
            self.api_root_url+'tokens/',
            auth=(username, password),
        )
        response.raise_for_status()
        return response.json().get('token')

    def create_user(self, data):
        return self._post_object(
            data,
            'users/')

    def get_user_index(self, query_string=None):
        url = 'users/'
        params = {}
        if query_string:
            params['q'] = query_string
        return self._get_object_index(url, params=params)

    def update_user(self, user_id, data_update):
        return self._patch_object(
            data_update,
            'users/%s/' % user_id)

    def delete_user(self, user_id):
        self._delete_object('users/%s/' % user_id)
