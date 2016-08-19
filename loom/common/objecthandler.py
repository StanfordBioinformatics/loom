import json
import requests
import time
import datetime
from loom.common.exceptions import *

def disable_insecure_request_warning():
    """Suppress warning about untrusted SSL certificate."""
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ObjectHandler(object):
    """ObjectHandler provides functions to create and work with objects in the 
    Loom database via the HTTP API
    """

    def __init__(self, master_url):
        self.api_root_url = master_url + '/api/'

    # ---- General methods ----
    
    def _post(self, data, relative_url, raise_for_status=True):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.post(
                url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
                verify=False),
            raise_for_status=raise_for_status)

    def _put(self, data, relative_url, raise_for_status=True):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.put(
                url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
                verify=False),
            raise_for_status=raise_for_status)

    def _patch(self, data, relative_url, raise_for_status=True):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(
            lambda: requests.patch(
                url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
                verify=False),
            raise_for_status=raise_for_status)

    def _get(self, relative_url, raise_for_status=True):
        url = self.api_root_url + relative_url
        disable_insecure_request_warning()
        return self._make_request_to_server(lambda: requests.get(url, verify=False), raise_for_status=raise_for_status) # Don't fail on unrecognized SSL certificate

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
        return self._post(object_data, relative_url, raise_for_status=True).json()

    def _put_object(self, object_data, relative_url):
        return self._put(object_data, relative_url, raise_for_status=True).json()

    def _patch_object(self, object_data, relative_url):
        return self._patch(object_data, relative_url, raise_for_status=True).json()

    def _get_object(self, relative_url, raise_for_status=True):
        response = self._get(relative_url, raise_for_status=raise_for_status)
        if response.status_code == 404:
            return None
        elif response.status_code == 200:
            return response.json()
        else:
            raise BadResponseError("Status code %s. %s" % (response.status_code, response.text))

    def _get_object_index(self, relative_url, raise_for_status=True):
        response = self._get(relative_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise BadResponseError("Status code %s." % response.status_code)

    # ---- Post/Put/Get [object_type] methods ----

    def post_data_object(self, data_object):
        return self._post_object(
            data_object,
            'data-objects/')

    def update_data_object(self, data_object_id, data_object_update):
        return self._put_object(
            data_object_update,
            'data-objects/%s/' % data_object_id)

    def get_file_data_object(self, file_id):
        return self._get_object(
            'file-data-objects/%s/' % file_id)

    def get_file_data_object_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'file-data-objects/?q='+query_string
        else:
            url = 'file-data-objects/'
        file_data_objects =  self._get_object_index(url)
        if len(file_data_objects) < min:
            raise IdMatchedTooFewFileDataObjectsError('Found %s FileDataObjects, expected at least %s' %(len(file_data_objects), min))
        if len(file_data_objects) > max:
            raise IdMatchedTooManyFileDataObjectsError('Found %s FileDataObjects, expected at most %s' %(len(file_data_objects), max))
        return file_data_objects

    def get_file_locations_by_file(self, file_id):
        return self._get_object(
            'file-data-objects/'+file_id+'/file-locations/'
        )

    def post_file_location(self, file_location):
        return self._post_object(
            file_location,
            'file-locations/')

    def update_file_location(self, file_location_id, file_location_update):
        return self._put_object(
            file_location_update,
            'file-locations/%s/' % file_location_id)

    def get_file_imports_by_file(self, file_id):
        return self._get_object_index(
            'file-data-objects/' + file_id + '/file-imports/'
        )
    
    def get_abstract_workflow(self, workflow_id):
        return self._get_object(
            'abstract-workflows/%s/' % workflow_id
        )

    def get_abstract_workflow_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'abstract-workflows/?q='+query_string
        else:
            url = 'abstract-workflows/'
        workflows = self._get_object_index(url)
        if len(workflows) < min:
            raise Error('Found %s workflows, expected at least %s' %(len(workflows), min))
        if len(workflows) > max:
            raise Error('Found %s workflows, expected at most %s' %(len(workflows), max))
        return workflows

    def post_abstract_workflow(self, workflow):
        return self._post_object(
            workflow,
            'abstract-workflows/')

    def get_workflow_run(self, workflow_run_id):
        return self._get_object(
            'workflow-runs/%s/' % workflow_run_id
        )

    def get_workflow_run_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'workflow-runs/?q='+query_string
        else:
            url = 'workflow-runs/'
        workflow_runs = self._get_object_index(url)
        if len(workflow_runs) < min:
            raise Error('Found %s workflow runs, expected at least %s' %(len(workflow_runs), min))
        if len(workflow_runs) > max:
            raise Error('Found %s workflow runs, expected at most %s' %(len(workflow_runs), max))
        return workflow_runs

    def post_workflow_run(self, workflow_run):
        return self._post_object(
            workflow_run,
            'workflow-runs/')

    def post_run_request(self, run_request):
        return self._post_object(
            run_request,
            'run-requests/')

    def get_run_request_index(self, query_string='', min=0, max=float('inf')):
        if query_string:
            url = 'run-requests/?q='+query_string
        else:
            url = 'run-requests/'
        run_requests = self._get_object_index(url)['run_requests']
        if len(run_requests) < min:
            raise Error('Found %s run requests, expected at least %s' %(len(run_requests), min))
        if len(run_requests) > max:
            raise Error('Found %s run requests, expected at most %s' %(len(run_requests), max))
        return run_requests

    def post_task_run(self, task_run):
        return self._post_object(
            task_run,
            'task-runs/')

    def get_task_run_attempt(self, task_run_attempt_id):
        return self._get_object(
            'task-run-attempts/%s/' % task_run_attempt_id,
            raise_for_status=True
        )

    def update_task_run_attempt(self, task_run_attempt_id, task_run_attempt_update):
        return self._put_object(
            task_run_attempt_update,
            'task-run-attempts/%s/' % task_run_attempt_id)

    def get_task_run_attempt_output(self, task_run_attempt_output_id):
        return self._get_object(
            'task-run-attempt-outputs/%s/' % task_run_attempt_output_id
        )

    def update_task_run_attempt_output(self, task_run_attempt_output_id, task_run_attempt_output_update):
        return self._put_object(
            task_run_attempt_output_update,
            'task-run-attempt-outputs/%s/' % task_run_attempt_output_id)

    def post_task_run_attempt_log_file(self, task_run_attempt_id, task_run_attempt_log_file):
        return self._post_object(
            task_run_attempt_log_file,
            'task-run-attempts/%s/task-run-attempt-log-files/' % task_run_attempt_id
        )

    def post_abstract_file_import(self, file_import):
        return self._post_object(
            file_import,
            'abstract-file-imports/')

    def update_abstract_file_import(self, file_import_id, file_import_update):
        return self._put_object(
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
            'task-run-attempts/%s/worker-settings/' % attempt_id
        )

    def get_filehandler_settings(self):
        return self._get_object(
            'filehandler-settings/'
        )
