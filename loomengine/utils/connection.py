import json
import requests
import time
import datetime
from loomengine.utils.exceptions import *

class TASK_ATTEMPT_STATUSES:
    NOT_STARTED = 'Not started'
    PROVISIONING_HOST = 'Provisioning host'
    LAUNCHING_MONITOR = 'Launching monitor process on worker'
    INITIALIZING_MONITOR = 'Initializing monitor process on worker'
    COPYING_INPUTS = 'Copying input files to runtime environment'
    CREATING_RUN_SCRIPT = 'Creating run script'
    FETCHING_IMAGE = 'Fetching runtime environment image'
    CREATING_CONTAINER = 'Creating runtime environment container'
    STARTING_ANALYSIS = 'Starting analysis'
    RUNNING_ANALYSIS = 'Running analysis'
    SAVING_OUTPUTS = 'Saving outputs'
    FINISHED = 'Finished'

def disable_insecure_request_warning():
    """Suppress warning about untrusted SSL certificate."""
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Connection(object):
    """Connection provides functions to create and work with objects in the 
    Loom database via the HTTP API
    """

    def __init__(self, master_url):
        self.api_root_url = master_url + '/api/'

    # ---- General methods ----
    
    def _post(self, data, relative_url):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.post(
                url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
                verify=False))

    def _put(self, data, relative_url):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.put(
                url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
                verify=False))

    def _patch(self, data, relative_url):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.patch(
                url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
                verify=False))

    def _get(self, relative_url, raise_for_status=True):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.get(
                url,
                verify=False), # Don't fail on unrecognized SSL certificate
            raise_for_status=raise_for_status)

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
                    try:
                        response.raise_for_status()
                    except requests.exceptions.HTTPError as e:
                        error = BadResponseError("%s\n%s" % (e.message, response.text))
            except requests.exceptions.ConnectionError as e:
                error = ServerConnectionError("No response from server.\n%s" % e.message)
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

    def _get_object(self, relative_url):
        # Do not raise_for_status, because we want to check for 404 here
        response = self._get(relative_url, raise_for_status=False)
        if response.status_code == 404:
            return None
        elif response.status_code == 200:
            return response.json()
        else:
            raise BadResponseError("Status code %s. %s" % (response.status_code, response.text))

    def _get_object_index(self, relative_url):
        response = self._get(relative_url)
        return response.json()

    # ---- Post/Put/Get [object_type] methods ----

    def post_data_object(self, data):
        return self._post_object(
            data,
            'data-objects/')
        
    def get_data_object(self, file_id):
        return self._get_object(
            'data-objects/%s/' % file_id)

    def get_data_object_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'data-objects/?q='+query_string
        else:
            url = 'data-objects/'
        data_objects =  self._get_object_index(url)
        if len(data_objects) < min:
            raise IdMatchedTooFewFileDataObjectsError(
                'Found %s DataObjects, expected at least %s' \
                % (len(data_objects), min))
        if len(data_objects) > max:
            raise IdMatchedTooManyFileDataObjectsError(
                'Found %s DataObjects, expected at most %s' \
                % (len(data_objects), max))
        return data_objects

#    def get_file_resources_by_file(self, file_id):
#        return self._get_object(
#            'files/'+file_id+'/file-resources/'
#        )

#    def post_file_resource(self, file_resource):
#        return self._post_object(
#            file_resource,
#            'file-resources/')

    def update_file_resource(self, file_resource_id, file_resource_update):
        return self._patch_object(
            file_resource_update,
            'file-resources/%s/' % file_resource_id)

    def get_file_imports_by_file(self, file_id):
        return self._get_object_index(
            'files/' + file_id + '/file-imports/'
        )
    
    def get_template(self, template_id):
        return self._get_object(
            'templates/%s/' % template_id
        )

    def get_template_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'templates/?q='+query_string
        else:
            url = 'templates/'
        templates = self._get_object_index(url)
        if len(templates) < min:
            raise Error('Found %s templates, expected at least %s' %(len(templates), min))
        if len(templates) > max:
            raise Error('Found %s templates, expected at most %s' %(len(templates), max))
        return templates

    def post_template(self, template):
        return self._post_object(
            template,
            'templates/')

    def get_template_run(self, template_run_id):
        return self._get_object(
            'runs/%s/' % template_run_id
        )

    def get_template_run_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'runs/?q='+query_string
        else:
            url = 'runs/'
        template_runs = self._get_object_index(url)
        if len(template_runs) < min:
            raise Error('Found %s template runs, expected at least %s' %(len(template_runs), min))
        if len(template_runs) > max:
            raise Error('Found %s template runs, expected at most %s' %(len(template_runs), max))
        return template_runs

    def post_template_run(self, template_run):
        return self._post_object(
            template_run,
            'runs/')

    def post_run_request(self, run_request):
        return self._post_object(
            run_request,
            'run-requests/')

    def get_run_request_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'run-requests/?q='+query_string
        else:
            url = 'run-requests/'
        run_requests = self._get_object_index(url)
        if len(run_requests) < min:
            raise Error('Found %s run requests, expected at least %s' %(len(run_requests), min))
        if len(run_requests) > max:
            raise Error('Found %s run requests, expected at most %s' %(len(run_requests), max))
        return run_requests

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
            'task-attempt-outputs/%s/' % task_attempt_output_id
        )

    def update_task_attempt_output(self, task_attempt_output_id, task_attempt_output_update):
        print task_attempt_output_update
        return self._patch_object(
            task_attempt_output_update,
            'task-attempt-outputs/%s/' % task_attempt_output_id)

    def post_task_attempt_log_file(self, task_attempt_id, task_attempt_log_file):
        return self._post_object(
            task_attempt_log_file,
            'task-attempts/%s/task-attempt-log-files/' % task_attempt_id
        )

    def post_task_attempt_error(self, task_attempt_id, task_attempt_error):
        return self._post_object(
            task_attempt_error,
            'task-attempts/%s/task-attempt-errors/' % task_attempt_id
        )

    def post_abstract_file_import(self, file_import):
        return self._post_object(
            file_import,
            'abstract-file-imports/')

    def update_abstract_file_import(self, file_import_id, file_import_update):
        return self._patch_object(
            file_import_update,
            'abstract-file-imports/%s/' % file_import_id)

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

    def get_worker_settings(self, attempt_id):
        return self._get_object(
            'task-attempts/%s/worker-settings/' % attempt_id
        )

    def get_filemanager_settings(self):
        return self._get_object(
            'filemanager-settings/'
        )
