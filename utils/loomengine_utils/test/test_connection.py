import datetime
import requests
import unittest

from loomengine_utils import connection
from loomengine_utils.exceptions import *


def MockResponse(status_code=200, content='{"mock": "data"}'):
    response = requests.Response()
    response.status_code = status_code
    response._content = content
    return response


class MockConnection(connection.Connection):
    # Overrides connection.Connection methods that need a server
    # with mock methods

    def __init__(self, server_url, token=None):
        self.token = token
        self.response = MockResponse()

    def _get(self, relative_url, raise_for_status=True, params=None):
        if params is None:
            params = {}
        self.method = 'GET'
        self.url = relative_url
        self.params = params
        return self.response

    def _post(self, data, relative_url, auth=None):
        self.method = 'POST'
        self.data = data
        self.url = relative_url
        self.auth = auth
        return self.response

    def _put(self, data, relative_url):
        self.method = 'PUT'
        self.data = data
        self.url = relative_url
        return self.response

    def _patch(self, data, relative_url):
        self.method = 'PATCH'
        self.data = data
        self.url = relative_url
        return self.response

    def _delete(self, relative_url, raise_for_status=True):
        self.method = 'DELETE'
        self.url = relative_url
        return self.response

def _raise_connection_error():
    raise requests.exceptions.ConnectionError
    
def _get_fail_then_pass_function(timelimit=0.5, status_code=200):
        """This raises a ConnectionError until {{timelimit}}
        seconds from now, after which it will return a MockResponse
        with status_code 200. Useful for testing the retry mechanism.
        """
        tick = datetime.datetime.now()
        return lambda: MockResponse(status_code=status_code) if \
            (datetime.datetime.now() - tick).total_seconds() >= timelimit\
            else _raise_connection_error()


class TestConnection(unittest.TestCase):

    mock_data = {'mock', 'data'}
    token = '12345abcde'

    def setUp(self):
        self.connection = MockConnection('root_url', token=self.token)

    def testAddAuthTokenToHeaders(self):
        headers = {'header1': 'header1_value'}
        new_headers = self.connection._add_auth_token_to_headers(headers)
        self.assertTrue(new_headers['header1'], 'header1_value')
        self.assertTrue(new_headers['Authorization'], 'Token '+self.token)

    def testMakeRequestToServerPassOnFirstTry(self):
        passing_function = _get_fail_then_pass_function(timelimit=0)
        response = self.connection._make_request_to_server(passing_function)
        self.assertEqual(response.status_code, 200)

    def testMakeRequestToServerPassOnRetry(self):
        # fail_then_pass_function will fail for {{fail_until}} seconds.
        # But connection._make_request_to_server will silently retry
        # until it succeeds.
        fail_until = 0.2
        tick = datetime.datetime.now()
        fail_then_pass_function = _get_fail_then_pass_function(timelimit=fail_until)
        response = self.connection._make_request_to_server(
            fail_then_pass_function,
            time_limit_seconds=1,
            retry_delay_seconds=0.05)
        tock = datetime.datetime.now()
        self.assertEqual(response.status_code, 200)
        self.assertTrue((tock-tick).total_seconds() > fail_until)

    def testMakeRequestToServerFailForStatus(self):
        with self.assertRaises(requests.exceptions.HTTPError):
            response = self.connection._make_request_to_server(
                lambda: MockResponse(status_code=500))

    def testPostResource(self):
        data = {'id': 1, 'name': 'test'}
        url = '/widgets/'
        response_json = self.connection._post_resource(data, url)
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.url, url)
        self.assertEqual(response_json, self.connection.response.json())

    def testPatchResource(self):
        data = {'id': 1, 'name': 'test'}
        url = '/widgets/001/'
        response_json = self.connection._patch_resource(data, url)
        self.assertEqual(self.connection.method, 'PATCH')
        self.assertEqual(self.connection.url, url)
        self.assertEqual(response_json, self.connection.response.json())

    def testDeleteResource(self):
        url = '/widgets/001/'
        response_json = self.connection._delete_resource(url)
        self.assertEqual(self.connection.method, 'DELETE')
        self.assertEqual(self.connection.url, url)
        self.assertEqual(response_json, self.connection.response.json())
        
    def testGetResource(self):
        url = '/widgets/001'
        params = {'param1': 'value1'}
        response_json = self.connection._get_resource(url, params=params)
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.url, url)
        self.assertEqual(self.connection.params, params)
        self.assertEqual(response_json, self.connection.response.json())

    def testGetResourceWhenNoneExists(self):
        url = '/widgets/001'
        self.connection.response = MockResponse(status_code=404)
        response_json = self.connection._get_resource(url)
        self.assertEqual(response_json, None)

    def testGetResourceWithErrorStatusCode(self):
        url = '/widgets/001'
        self.connection.response = MockResponse(status_code=500)
        with self.assertRaises(requests.exceptions.HTTPError):
            response_json = self.connection._get_resource(url)

    def testGetIndex(self):
        url = '/widgets/'
        params = {'param1': 'value1'}
        response_json = self.connection._get_index(url, params=params)
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.url, url)
        self.assertEqual(self.connection.params, params)
        self.assertEqual(response_json, self.connection.response.json())

    # ------------------ Resource-specific methods ---------------------
        
    # DataNode

    def testGetDataNode(self):
        response_json = self.connection.get_data_node('123')
        self.assertEqual(self.connection.url, 'data-nodes/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataNodeExpand(self):
        response_json = self.connection.get_data_node('123', expand=True)
        self.assertEqual(self.connection.url, 'data-nodes/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {'expand': '1'})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataNodeIndex(self):
        response_json = self.connection.get_data_node_index()
        self.assertEqual(self.connection.url, 'data-nodes/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    # DataObject

    def testPostDataObject(self):
        response_json = self.connection.post_data_object(self.mock_data)
        self.assertEqual(self.connection.url, 'data-objects/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataObject(self):
        response_json = self.connection.get_data_object('123')
        self.assertEqual(self.connection.url, 'data-objects/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testUpdateDataObject(self):
        response_json = self.connection.update_data_object('123', self.mock_data)
        self.assertEqual(self.connection.url, 'data-objects/123/')
        self.assertEqual(self.connection.method, 'PATCH')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testDeleteDataObject(self):
        response_json = self.connection.delete_data_object('123')
        self.assertEqual(self.connection.url, 'data-objects/123/')
        self.assertEqual(self.connection.method, 'DELETE')
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataObjectIndex(self):
        response_json = self.connection.get_data_object_index()
        self.assertEqual(self.connection.url, 'data-objects/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataObjectIndexWithParams(self):
        response_json = self.connection.get_data_object_index(
            query_string='query',
            source_type='imported',
            labels=['label1',],
            type='string',
            min=1,
            max=10)
        self.assertEqual(self.connection.url, 'data-objects/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {
            'q': 'query', 'source_type': 'imported',
            'type': 'string', 'labels': 'label1'})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataObjectIndexTooFew(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        with self.assertRaises(ResourceCountError):
            self.connection.get_data_object_index(min=3, max=10)

    def testGetDataObjectIndexTooMany(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        with self.assertRaises(ResourceCountError):
            self.connection.get_data_object_index(min=0, max=1)

    def testGetDataObjectIndexWithLimit(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        response_json = self.connection.get_data_object_index_with_limit()
        self.assertEqual(self.connection.url, 'data-objects/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {'limit': 10, 'offset': 0})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataObjectIndexWithLimitWithParams(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        response_json = self.connection.get_data_object_index_with_limit(
            limit=2, offset=4,
            query_string='query',
            source_type='imported',
            labels=['label1',],
            type='string')
        self.assertEqual(self.connection.url, 'data-objects/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {
            'limit': 2, 'offset': 4, 'q': 'query',
            'source_type': 'imported', 'type': 'string', 'labels': 'label1'})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetDataObjectDependencies(self):
        response_json = self.connection.get_data_object_dependencies('123')
        self.assertEqual(self.connection.url, 'data-objects/123/dependencies/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testPostDataTag(self):
        response_json = self.connection.post_data_tag('123', self.mock_data)
        self.assertEqual(self.connection.url, 'data-objects/123/add-tag/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testRemoveDataTag(self):
        response_json = self.connection.remove_data_tag('123', self.mock_data)
        self.assertEqual(self.connection.url, 'data-objects/123/remove-tag/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testListDataTags(self):
        response_json = self.connection.list_data_tags('123')
        self.assertEqual(self.connection.url, 'data-objects/123/tags/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(response_json, self.connection.response.json())

    def testPostDataLabel(self):
        response_json = self.connection.post_data_label('123', self.mock_data)
        self.assertEqual(self.connection.url, 'data-objects/123/add-label/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testRemoveDataLabel(self):
        response_json = self.connection.remove_data_label('123', self.mock_data)
        self.assertEqual(self.connection.url, 'data-objects/123/remove-label/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testListDataLabels(self):
        response_json = self.connection.list_data_labels('123')
        self.assertEqual(self.connection.url, 'data-objects/123/labels/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(response_json, self.connection.response.json())

    # Template

    def testPostTemplate(self):
        response_json = self.connection.post_template(self.mock_data)
        self.assertEqual(self.connection.url, 'templates/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplate(self):
        response_json = self.connection.get_template('123')
        self.assertEqual(self.connection.url, 'templates/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testDeleteTemplate(self):
        response_json = self.connection.delete_template('123')
        self.assertEqual(self.connection.url, 'templates/123/')
        self.assertEqual(self.connection.method, 'DELETE')
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplateIndex(self):
        response_json = self.connection.get_template_index()
        self.assertEqual(self.connection.url, 'templates/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplateIndexWithParams(self):
        response_json = self.connection.get_template_index(
            query_string='query',
            parent_only=True,
            labels=['label1',],
            min=1,
            max=10)
        self.assertEqual(self.connection.url, 'templates/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {
            'q': 'query', 'parent_only': '1',
            'labels': 'label1'})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplateIndexWithLimit(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        response_json = self.connection.get_template_index_with_limit()
        self.assertEqual(self.connection.url, 'templates/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {'limit': 10, 'offset': 0})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplateIndexWithLimitWithParams(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        response_json = self.connection.get_template_index_with_limit(
            query_string='query',
            limit=2, offset=4,
            parent_only=True,
            labels=['label1',])
        self.assertEqual(self.connection.url, 'templates/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {
            'limit': 2, 'offset': 4, 'q': 'query',
            'parent_only': '1', 'labels': 'label1'})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplateDependencies(self):
        response_json = self.connection.get_template_dependencies('123')
        self.assertEqual(self.connection.url, 'templates/123/dependencies/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testPostTemplateTag(self):
        response_json = self.connection.post_template_tag('123', self.mock_data)
        self.assertEqual(self.connection.url, 'templates/123/add-tag/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testRemoveTemplateTag(self):
        response_json = self.connection.remove_template_tag('123', self.mock_data)
        self.assertEqual(self.connection.url, 'templates/123/remove-tag/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testListTemplateTags(self):
        response_json = self.connection.list_template_tags('123')
        self.assertEqual(self.connection.url, 'templates/123/tags/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(response_json, self.connection.response.json())

    def testPostTemplateLabel(self):
        response_json = self.connection.post_template_label('123', self.mock_data)
        self.assertEqual(self.connection.url, 'templates/123/add-label/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testRemoveTemplateLabel(self):
        response_json = self.connection.remove_template_label('123', self.mock_data)
        self.assertEqual(self.connection.url, 'templates/123/remove-label/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testListTemplateLabels(self):
        response_json = self.connection.list_template_labels('123')
        self.assertEqual(self.connection.url, 'templates/123/labels/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(response_json, self.connection.response.json())

    # Run

    def testGetRun(self):
        response_json = self.connection.get_run('123')
        self.assertEqual(self.connection.url, 'runs/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testDeleteRun(self):
        response_json = self.connection.delete_run('123')
        self.assertEqual(self.connection.url, 'runs/123/')
        self.assertEqual(self.connection.method, 'DELETE')
        self.assertEqual(response_json, self.connection.response.json())

    def testGetRunIndex(self):
        response_json = self.connection.get_run_index()
        self.assertEqual(self.connection.url, 'runs/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetRunIndexWithParams(self):
        response_json = self.connection.get_run_index(
            query_string='query',
            parent_only=True,
            labels=['label1',],
            min=1,
            max=10)
        self.assertEqual(self.connection.url, 'runs/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {
            'q': 'query', 'parent_only': '1',
            'labels': 'label1'})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetRunIndexWithLimit(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        response_json = self.connection.get_run_index_with_limit()
        self.assertEqual(self.connection.url, 'runs/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {'limit': 10, 'offset': 0})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetRunIndexWithLimitWithParams(self):
        self.connection.response = MockResponse(
            status_code=200, content='[{"id":"1"},{"id":"2"}]')
        response_json = self.connection.get_run_index_with_limit(
            query_string='query',
            limit=2, offset=4,
            parent_only=True,
            labels=['label1',])
        self.assertEqual(self.connection.url, 'runs/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {
            'limit': 2, 'offset': 4, 'q': 'query',
            'parent_only': '1', 'labels': 'label1'})
        self.assertEqual(len(response_json), 2)

    def testKillRun(self):
        response_json = self.connection.kill_run('123')
        self.assertEqual(self.connection.url, 'runs/123/kill/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(response_json, self.connection.response.json())

    def testGetRunDependencies(self):
        response_json = self.connection.get_run_dependencies('123')
        self.assertEqual(self.connection.url, 'runs/123/dependencies/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testPostRunTag(self):
        response_json = self.connection.post_run_tag('123', self.mock_data)
        self.assertEqual(self.connection.url, 'runs/123/add-tag/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testRemoveRunTag(self):
        response_json = self.connection.remove_run_tag('123', self.mock_data)
        self.assertEqual(self.connection.url, 'runs/123/remove-tag/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testListRunTags(self):
        response_json = self.connection.list_run_tags('123')
        self.assertEqual(self.connection.url, 'runs/123/tags/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(response_json, self.connection.response.json())

    def testPostRunLabel(self):
        response_json = self.connection.post_run_label('123', self.mock_data)
        self.assertEqual(self.connection.url, 'runs/123/add-label/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testRemoveRunLabel(self):
        response_json = self.connection.remove_run_label('123', self.mock_data)
        self.assertEqual(self.connection.url, 'runs/123/remove-label/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testListRunLabels(self):
        response_json = self.connection.list_run_labels('123')
        self.assertEqual(self.connection.url, 'runs/123/labels/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(response_json, self.connection.response.json())

    # Task

    def testGetTask(self):
        response_json = self.connection.get_task('123')
        self.assertEqual(self.connection.url, 'tasks/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    # TaskAttempt

    def testGetTaskAttempt(self):
        response_json = self.connection.get_task_attempt('123')
        self.assertEqual(self.connection.url, 'task-attempts/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testUpdateTaskAttempt(self):
        response_json = self.connection.update_task_attempt('123', self.mock_data)
        self.assertEqual(self.connection.url, 'task-attempts/123/')
        self.assertEqual(self.connection.method, 'PATCH')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())
        
    def testGetTaskAttemptOutput(self):
        response_json = self.connection.get_task_attempt_output('123')
        self.assertEqual(self.connection.url, 'outputs/123/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testUpdateTaskAttemptOutput(self):
        response_json = self.connection.update_task_attempt_output(
            '123', self.mock_data)
        self.assertEqual(self.connection.url, 'outputs/123/')
        self.assertEqual(self.connection.method, 'PATCH')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testPostTaskAttemptLogFile(self):
        response_json = self.connection.post_task_attempt_log_file(
            '123', self.mock_data)
        self.assertEqual(self.connection.url, 'task-attempts/123/log-files/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testPostTaskAttemptLogFileDataObject(self):
        response_json = self.connection.post_task_attempt_log_file_data_object(
            '123', self.mock_data)
        self.assertEqual(self.connection.url, 'log-files/123/data-object/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testPostTaskAttemptEvent(self):
        response_json = self.connection.post_task_attempt_event(
            '123', self.mock_data)
        self.assertEqual(self.connection.url, 'task-attempts/123/events/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testPostTaskAttemptSystemError(self):
        response_json = self.connection.post_task_attempt_system_error(
            '123')
        self.assertEqual(self.connection.url, 'task-attempts/123/system-error/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testPostTaskAttemptAnalysisError(self):
        response_json = self.connection.post_task_attempt_analysis_error(
            '123')
        self.assertEqual(self.connection.url, 'task-attempts/123/analysis-error/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testFinishTaskAttempt(self):
        response_json = self.connection.finish_task_attempt('123')
        self.assertEqual(self.connection.url, 'task-attempts/123/finish/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTaskAttemptSettings(self):
        response_json = self.connection.get_task_attempt_settings('123')
	self.assertEqual(self.connection.url, 'task-attempts/123/settings/')
	self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(response_json, self.connection.response.json())

    # User

    def testPostUser(self):
        response_json = self.connection.post_user(self.mock_data)
        self.assertEqual(self.connection.url, 'users/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testUpdateUser(self):
        response_json = self.connection.update_user('123', self.mock_data)
        self.assertEqual(self.connection.url, 'users/123/')
        self.assertEqual(self.connection.method, 'PATCH')
        self.assertEqual(self.connection.data, self.mock_data)
        self.assertEqual(response_json, self.connection.response.json())

    def testDeleteUser(self):
        response_json = self.connection.delete_user('123')
        self.assertEqual(self.connection.url, 'users/123/')
        self.assertEqual(self.connection.method, 'DELETE')
        self.assertEqual(response_json, self.connection.response.json())

    def testGetUserIndex(self):
        response_json = self.connection.get_user_index()
        self.assertEqual(self.connection.url, 'users/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    # Token

    def testCreateToken(self):
        token = '123abc'
        self.connection.response = MockResponse(
            status_code=200, content='{"token": "123abc"}')
        token_issued = self.connection.create_token(username='u', password='p')
        self.assertEqual(token_issued, token)
        self.assertEqual(self.connection.auth, ('u', 'p'))

    # Data/Template/Run Tag Index

    def testGetDataTagIndex(self):
        response_json = self.connection.get_data_tag_index()
        self.assertEqual(self.connection.url, 'data-tags/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplateTagIndex(self):
        response_json = self.connection.get_template_tag_index()
        self.assertEqual(self.connection.url, 'template-tags/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetRunTagIndex(self):
        response_json = self.connection.get_run_tag_index()
        self.assertEqual(self.connection.url, 'run-tags/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    # Data/Template/Run Label Index

    def testGetDataLabelIndex(self):
        response_json = self.connection.get_data_label_index()
        self.assertEqual(self.connection.url, 'data-labels/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetTemplateLabelIndex(self):
        response_json = self.connection.get_template_label_index()
        self.assertEqual(self.connection.url, 'template-labels/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    def testGetRunLabelIndex(self):
        response_json = self.connection.get_run_label_index()
        self.assertEqual(self.connection.url, 'run-labels/')
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.params, {})
        self.assertEqual(response_json, self.connection.response.json())

    # Info/Version/Settings

    def testGetInfo(self):
        response_json = self.connection.get_info()
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.url, 'info/')
        self.assertEqual(response_json, self.connection.response.json())

    def testGetInfoConnectionFailed(self):
        def _connection_failed():
            raise ServerConnectionError
        self.connection._get = lambda x: _connection_failed()
        info = self.connection.get_info()
        self.assertIsNone(info)

    def testGetVersion(self):
        self.connection.response = MockResponse(
            status_code=200, content='{"version":"123"}')
        version = self.connection.get_version()
        self.assertEqual(version, '123')

    def testGetVersionConnectionFailed(self):
        def _connection_failed():
            raise ServerConnectionError
        self.connection._get = lambda x: _connection_failed()
        version = self.connection.get_version()
        self.assertIsNone(version)

    def testGetStorageSettings(self):
        response_json = self.connection.get_storage_settings()
        self.assertEqual(self.connection.method, 'GET')
        self.assertEqual(self.connection.url, 'storage-settings/')
        self.assertEqual(response_json, self.connection.response.json())


if __name__ == '__main__':
    unittest.main()
