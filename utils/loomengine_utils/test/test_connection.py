import datetime
import json
import re
import requests
import unittest
import warnings

from loomengine_utils import connection
from loomengine_utils.exceptions import ServerConnectionError, ResourceCountError, ServerConnectionHttpError

class MockRoute:
    def __init__(self, route_regex, method, response, params=None):
        self.route_regex = route_regex
        self.method = method
        self.params = params
        self.response = response


class MockRequest:
    def __init__(self, url, method, params=None, data=None, auth=None):
        self.url = url
        self.method = method
        self.params = params
        self.data = data
        self.auth = auth

default_response_data = {"message": "default content"}

def MockResponse(status_code=200, content=None):
    if content is None:
        content = default_response_data
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(content)
    return response


class MockConnection(connection.Connection):
    # Overrides connection.Connection methods that need a server
    # with mock methods

    def __init__(self, server_url, token=None):
        super(MockConnection, self).__init__(server_url, token=token)
        self.requests = []
        self.routes = []
        self.default_response = None

    def add_route(self, route_regex, method, content=None,
                  status_code=200, params=None):
        self.routes.append(
            MockRoute(route_regex,
                      method,
                      MockResponse(status_code=status_code, content=content),
                      params=params))

    def set_default_response(self, status_code, content):
        self.default_response = MockResponse(
            status_code=status_code, content=content)
        
    def _add_request(self, relative_url, method,
                     params=None, data=None, auth=None):
        request = MockRequest(
            relative_url, method, params=params, data=data, auth=auth)
        self.requests.append(request)
        return request

    def _get_response(self, request):
        for route in self.routes:
            if re.match(route.route_regex, request.url) \
               and route.method == request.method \
               and route.params==request.params:
                return route.response
        # No matching route. Return Default.
        if self.default_response is not None:
            return self.default_response
        else:
            raise Exception(
                'Route not found: %s %s params=%s data=%s auth=%s'
                % (request.method, request.url, request.params,
                   request.data, request.auth))

    def _get(self, relative_url, raise_for_status=True,
             params=None, auth=None, timeout=30):
        if params == {}:
            # For MockRoutes, it is standard to use params=None, but
            # some Connection methods  set it to {}, so we standardize it here.
            params = None
        request = self._add_request(relative_url, 'GET', params=params, auth=auth)
        return self._get_response(request)

    def _post(self, data, relative_url, auth=None, timeout=30):
        request = self._add_request(relative_url, 'POST', data=data, auth=auth)
        return self._get_response(request)

    def _put(self, data, relative_url, auth=None, timeout=30):
        request = self._add_request(relative_url, 'PUT', data=data, auth=auth)
        return self._get_response(request)

    def _patch(self, data, relative_url, auth=None, timeout=30):
        request = self._add_request(relative_url, 'PATCH', data=data, auth=auth)
        return self._get_response(request)

    def _delete(self, relative_url, raise_for_status=True, auth=None, timeout=30):
        request = self._add_request(relative_url, 'DELETE', auth=auth)
        return self._get_response(request)

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

    mock_request_data = {'message': 'mock request data'}
    token = '12345abcde'

    def setUp(self):
        self.connection = MockConnection('root_url', token=self.token)

    def testDisableInsecureRequestWarning(self):
        # Warning will be raised as an error if not suppressed
        warnings.filterwarnings('error')
        with self.assertRaises(Exception):
            requests.get('https://www.google.com', verify=False)
        connection.disable_insecure_request_warning()
        requests.get('https://www.google.com', verify=False)

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
        fail_then_pass_function = _get_fail_then_pass_function(
            timelimit=fail_until)
        response = self.connection._make_request_to_server(
            fail_then_pass_function,
            time_limit_seconds=1,
            retry_delay_seconds=0.05)
        tock = datetime.datetime.now()
        self.assertEqual(response.status_code, 200)
        self.assertTrue((tock-tick).total_seconds() > fail_until)

    def testMakeRequestToServerFailForStatus(self):
        with self.assertRaises(ServerConnectionError):
            response = self.connection._make_request_to_server(
                lambda: MockResponse(status_code=500))

    def testPostResource(self):
        data = {'id': 1, 'name': 'test'}
        url = 'widgets/'
        self.connection.add_route(url, 'POST')
        response_data = self.connection._post_resource(data, url)
        self.assertEqual(response_data, default_response_data)

    def testPatchResource(self):
        data = {'id': 1, 'name': 'test'}
        url = 'widgets/001/'
        self.connection.add_route(url, 'PATCH')
        response_data = self.connection._patch_resource(data, url)
        self.assertEqual(response_data, default_response_data)

    def testDeleteResource(self):
        url = 'widgets/001/'
        self.connection.add_route(url, 'DELETE')
        response_data = self.connection._delete_resource(url)
        self.assertEqual(response_data, default_response_data)

    def testGetResource(self):
        url = 'widgets/001/'
        params = {'param1': 'value1'}
        self.connection.add_route(url, 'GET', params=params)
        response_data = self.connection._get_resource(url, params=params)
        self.assertEqual(response_data, default_response_data)

    def testGetResourceWhenNoneExists(self):
        url = 'widgets/001/'
        self.connection.add_route(url, 'GET', status_code=404)
        response_data = self.connection._get_resource(url)
        self.assertEqual(response_data, None)

    def testGetResourceWithErrorStatusCode(self):
        url = 'widgets/001/'
        self.connection.add_route(url, 'GET', status_code=500)
        with self.assertRaises(ServerConnectionHttpError):
            response_data = self.connection._get_resource(url)

    def testGetIndex(self):
        url = 'widgets/'
        params = {'param1': 'value1'}
        self.connection.add_route(url, 'GET', params=params)
        response_data = self.connection._get_index(url, params=params)
        self.assertEqual(response_data, default_response_data)

    # ------------------ Resource-specific methods ---------------------
        
    # DataNode

    def testGetDataNode(self):
        self.connection.add_route('data-nodes/123/', 'GET')
        response_data = self.connection.get_data_node('123')
        self.assertEqual(response_data, default_response_data)

    def testGetDataNodeExpand(self):
        self.connection.add_route('data-nodes/123/', 'GET', params={'expand': '1'})
        response_data = self.connection.get_data_node('123', expand=True)
        self.assertEqual(response_data, default_response_data)

    def testGetDataNodeIndex(self):
        self.connection.add_route('data-nodes/', 'GET')
        response_data = self.connection.get_data_node_index()
        self.assertEqual(response_data, default_response_data)

    # DataObject

    def testPostDataObject(self):
        self.connection.add_route('data-objects/', 'POST')
        response_data = self.connection.post_data_object(self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testGetDataObject(self):
        self.connection.add_route('data-objects/', 'GET')
        response_data = self.connection.get_data_object('123')
        self.assertEqual(response_data, default_response_data)

    def testUpdateDataObject(self):
        self.connection.add_route('data-objects/123/', 'PATCH')
        response_data = self.connection.update_data_object(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testDeleteDataObject(self):
        self.connection.add_route('data-objects/123/', 'DELETE')
        response_data = self.connection.delete_data_object('123')
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, None)

    def testGetDataObjectIndex(self):
        self.connection.add_route('data-objects/', 'GET')
        response_data = self.connection.get_data_object_index()
        self.assertEqual(response_data, default_response_data)

    def testGetDataObjectIndexWithParams(self):
        params = {'q': 'query', 'source_type': 'imported',
                  'labels': 'label1', 'type': 'string'}
        self.connection.add_route('data-objects/', 'GET', params=params)
        response_data = self.connection.get_data_object_index(
            query_string='query',
            source_type='imported',
            labels=['label1',],
            type='string',
            min=1,
            max=10)
        self.assertEqual(response_data, default_response_data)

    def testGetDataObjectIndexTooFew(self):
        self.connection.add_route(
            'data-objects/', 'GET', content=[{"id":"1"},{"id":"2"}], status_code=200)
        with self.assertRaises(ResourceCountError):
            self.connection.get_data_object_index(min=3, max=10)

    def testGetDataObjectIndexTooMany(self):
        self.connection.add_route(
            'data-objects/', 'GET', content=[{"id":"1"},{"id":"2"}], status_code=200)
        with self.assertRaises(ResourceCountError):
            self.connection.get_data_object_index(min=0, max=1)

    def testGetDataObjectIndexWithLimit(self):
        content = [{"id":"1"},{"id":"2"}]
        self.connection.add_route(
            'data-objects', 'GET', content=content, status_code=200,
            params={'limit': 10, 'offset': 0})
        response_data = self.connection.get_data_object_index_with_limit()
        self.assertEqual(response_data, content)

    def testGetDataObjectIndexWithLimitWithParams(self):
        content=[{"id":"1"},{"id":"2"}]
        self.connection.add_route(
            'data-objects/', 'GET', content=content, params={
                'limit': 2, 'offset': 4, 'q': 'query',
                'source_type': 'imported', 'type': 'string', 'labels': 'label1'})
        response_data = self.connection.get_data_object_index_with_limit(
            limit=2, offset=4,
            query_string='query',
            source_type='imported',
            labels=['label1',],
            type='string')
        self.assertEqual(response_data, content)

    def testGetDataObjectDependencies(self):
        self.connection.add_route('data-objects/123/dependencies/', 'GET')
        response_data = self.connection.get_data_object_dependencies('123')
        self.assertEqual(response_data, default_response_data)

    def testPostDataTag(self):
        self.connection.add_route('data-objects/123/add-tag/', 'POST')
        response_data = self.connection.post_data_tag('123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testRemoveDataTag(self):
        self.connection.add_route('data-objects/123/remove-tag/', 'POST')
        response_data = self.connection.remove_data_tag(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testListDataTags(self):
        self.connection.add_route('data-objects/123/tags/', 'GET')
        response_data = self.connection.list_data_tags('123')
        self.assertEqual(response_data, default_response_data)

    def testPostDataLabel(self):
        self.connection.add_route('data-objects/123/add-label/', 'POST')
        response_data = self.connection.post_data_label('123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testRemoveDataLabel(self):
        self.connection.add_route('data-objects/123/remove-label/', 'POST')
        response_data = self.connection.remove_data_label(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testListDataLabels(self):
        self.connection.add_route('data-objects/123/labels/', 'GET')
        response_data = self.connection.list_data_labels('123')
        self.assertEqual(response_data, default_response_data)

    # Template

    def testPostTemplate(self):
        self.connection.add_route('templates/', 'POST')
        response_data = self.connection.post_template(self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testGetTemplate(self):
        self.connection.add_route('templates/123/', 'GET')
        response_data = self.connection.get_template('123')
        self.assertEqual(response_data, default_response_data)

    def testDeleteTemplate(self):
        self.connection.add_route('templates/123/', 'DELETE')
        response_data = self.connection.delete_template('123')
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, None)

    def testGetTemplateIndex(self):
        self.connection.add_route('templates/', 'GET')
        response_data = self.connection.get_template_index()
        self.assertEqual(response_data, default_response_data)

    def testGetTemplateIndexWithParams(self):
        self.connection.add_route('templates/', 'GET', params={
            'q': 'query', 'parent_only': '1',
            'labels': 'label1'})
        response_data = self.connection.get_template_index(
            query_string='query',
            parent_only=True,
            labels=['label1',],
            min=1,
            max=10)
        self.assertEqual(response_data, default_response_data)

    def testGetTemplateIndexWithLimit(self):
        self.connection.add_route('templates/', 'GET', params={
            'limit': 10, 'offset': 0})
        response_data = self.connection.get_template_index_with_limit()
        self.assertEqual(response_data, default_response_data)

    def testGetTemplateIndexWithLimitWithParams(self):
        self.connection.add_route('templates/', 'GET', params={
            'limit': 2, 'offset': 4, 'q': 'query',
            'parent_only': '1', 'labels': 'label1'})
        response_data = self.connection.get_template_index_with_limit(
            query_string='query',
            limit=2, offset=4,
            parent_only=True,
            labels=['label1',])
        self.assertEqual(response_data, default_response_data)

    def testGetTemplateDependencies(self):
        self.connection.add_route('templates/123/dependencies/', 'GET')
        response_data = self.connection.get_template_dependencies('123')
        self.assertEqual(response_data, default_response_data)

    def testPostTemplateTag(self):
        self.connection.add_route('templates/123/add-tag/', 'POST')
        response_data = self.connection.post_template_tag('123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testRemoveTemplateTag(self):
        self.connection.add_route('templates/123/remove-tag/', 'POST')
        response_data = self.connection.remove_template_tag(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testListTemplateTags(self):
        self.connection.add_route('templates/123/tags/', 'GET')
        response_data = self.connection.list_template_tags('123')
        self.assertEqual(response_data, default_response_data)

    def testPostTemplateLabel(self):
        self.connection.add_route('templates/123/add-label/', 'POST')
        response_data = self.connection.post_template_label(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(
            self.connection.requests[0].data, self.mock_request_data)

    def testRemoveTemplateLabel(self):
        self.connection.add_route('templates/123/remove-label/', 'POST')
        response_data = self.connection.remove_template_label(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testListTemplateLabels(self):
        self.connection.add_route('templates/123/labels/', 'GET')
        response_data = self.connection.list_template_labels('123')
        self.assertEqual(self.connection.requests[0].method, 'GET')
        self.assertEqual(response_data, default_response_data)

    # Run

    def testPostRun(self):
        self.connection.add_route('runs/', 'POST')
        response_data = self.connection.post_run(self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testGetRun(self):
        self.connection.add_route('runs/123/', 'GET')
        response_data = self.connection.get_run('123')
        self.assertEqual(response_data, default_response_data)

    def testDeleteRun(self):
        self.connection.add_route('runs/123/', 'DELETE')
        response_data = self.connection.delete_run('123')
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, None)

    def testGetRunIndex(self):
        self.connection.add_route('runs/', 'GET')
        response_data = self.connection.get_run_index()
        self.assertEqual(response_data, default_response_data)

    def testGetRunIndexWithParams(self):
        self.connection.add_route('runs/', 'GET', params={
            'q': 'query', 'parent_only': '1',
            'labels': 'label1'})
        response_data = self.connection.get_run_index(
            query_string='query',
            parent_only=True,
            labels=['label1',],
            min=1,
            max=10)
        self.assertEqual(response_data, default_response_data)

    def testGetRunIndexWithLimit(self):
        content = [{"id":"1"},{"id":"2"}]
        self.connection.add_route('runs/', 'GET', params={
            'limit': 10, 'offset': 0}, content=content)
        response_data = self.connection.get_run_index_with_limit()
        self.assertEqual(response_data, content)

    def testGetRunIndexWithLimitWithParams(self):
        content = [{"id":"1"},{"id":"2"}]
        self.connection.add_route(
            'runs/', 'GET', content=content, status_code=200,
            params={
                'limit': 2, 'offset': 4, 'q': 'query',
                'parent_only': '1', 'labels': 'label1'})
        response_data = self.connection.get_run_index_with_limit(
            query_string='query',
            limit=2, offset=4,
            parent_only=True,
            labels=['label1',])
        self.assertEqual(self.connection.requests[0].url, 'runs/')
        self.assertEqual(self.connection.requests[0].method, 'GET')
        self.assertEqual(self.connection.requests[0].params, {
            'limit': 2, 'offset': 4, 'q': 'query',
            'parent_only': '1', 'labels': 'label1'})
        self.assertEqual(response_data, content)

    def testKillRun(self):
        self.connection.add_route('runs/123/kill/', 'POST')
        response_data = self.connection.kill_run('123')
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, {})

    def testGetRunDependencies(self):
        self.connection.add_route('runs/123/dependencies/', 'GET')
        response_data = self.connection.get_run_dependencies('123')
        self.assertEqual(response_data, default_response_data)

    def testPostRunTag(self):
        self.connection.add_route('runs/123/add-tag/', 'POST')
        response_data = self.connection.post_run_tag('123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testRemoveRunTag(self):
        self.connection.add_route('runs/123/remove-tag/', 'POST')
        response_data = self.connection.remove_run_tag(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testListRunTags(self):
        self.connection.add_route('runs/123/tags/', 'GET')
        response_data = self.connection.list_run_tags('123')
        self.assertEqual(response_data, default_response_data)

    def testPostRunLabel(self):
        self.connection.add_route('runs/123/add-label/', 'POST')
        response_data = self.connection.post_run_label('123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testRemoveRunLabel(self):
        self.connection.add_route('runs/123/remove-label/', 'POST')
        response_data = self.connection.remove_run_label(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testListRunLabels(self):
        self.connection.add_route('runs/123/labels/', 'GET')
        response_data = self.connection.list_run_labels('123')
        self.assertEqual(response_data, default_response_data)

    # Task

    def testGetTask(self):
        self.connection.add_route('tasks/123/', 'GET')
        response_data = self.connection.get_task('123')
        self.assertEqual(response_data, default_response_data)

    # TaskAttempt

    def testGetTaskAttempt(self):
        self.connection.add_route('task-attempts/123/', 'GET')
        response_data = self.connection.get_task_attempt('123')
        self.assertEqual(response_data, default_response_data)

    def testUpdateTaskAttempt(self):
        self.connection.add_route('task-attempts/123/', 'PATCH')
        response_data = self.connection.update_task_attempt(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)
        
    def testGetTaskAttemptOutput(self):
        self.connection.add_route('outputs/123/', 'GET')
        response_data = self.connection.get_task_attempt_output('123')
        self.assertEqual(response_data, default_response_data)

    def testUpdateTaskAttemptOutput(self):
        self.connection.add_route('outputs/123/', 'PATCH')
        response_data = self.connection.update_task_attempt_output(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testPostTaskAttemptLogFile(self):
        self.connection.add_route('task-attempts/123/log-files/', 'POST')
        response_data = self.connection.post_task_attempt_log_file(
            '123', self.mock_request_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)
        self.assertEqual(response_data, default_response_data)

    def testPostTaskAttemptLogFileDataObject(self):
        self.connection.add_route('log-files/123/data-object/', 'POST')
        response_data = self.connection.post_task_attempt_log_file_data_object(
            '123', self.mock_request_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)
        self.assertEqual(response_data, default_response_data)

    def testPostTaskAttemptEvent(self):
        self.connection.add_route('task-attempts/123/events/', 'POST')
        response_data = self.connection.post_task_attempt_event(
            '123', self.mock_request_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)
        self.assertEqual(response_data, default_response_data)

    def testPostTaskAttemptSystemError(self):
        self.connection.add_route('task-attempts/123/system-error/', 'POST')
        response_data = self.connection.post_task_attempt_system_error(
            '123')
        self.assertEqual(self.connection.requests[0].data, {})
        self.assertEqual(response_data, default_response_data)

    def testPostTaskAttemptAnalysisError(self):
        self.connection.add_route('task-attempts/123/analysis-error/', 'POST')
        response_data = self.connection.post_task_attempt_analysis_error(
            '123')
        self.assertEqual(self.connection.requests[0].data, {})
        self.assertEqual(response_data, default_response_data)

    def testFinishTaskAttempt(self):
        self.connection.add_route('task-attempts/123/finish/', 'POST')
        response_data = self.connection.finish_task_attempt('123')
        self.assertEqual(self.connection.requests[0].data, {})
        self.assertEqual(response_data, default_response_data)

    def testGetTaskAttemptSettings(self):
        self.connection.add_route('task-attempts/123/settings/', 'GET')
        response_data = self.connection.get_task_attempt_settings('123')
        self.assertEqual(response_data, default_response_data)

    # User

    def testPostUser(self):
        self.connection.add_route('users/', 'POST')
        response_data = self.connection.post_user(self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testUpdateUser(self):
        self.connection.add_route('users/123/', 'PATCH')
        response_data = self.connection.update_user(
            '123', self.mock_request_data)
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, self.mock_request_data)

    def testDeleteUser(self):
        self.connection.add_route('users/123/', 'DELETE')
        response_data = self.connection.delete_user('123')
        self.assertEqual(response_data, default_response_data)
        self.assertEqual(self.connection.requests[0].data, None)

    def testGetUserIndex(self):
        self.connection.add_route('users/', 'GET')
        response_data = self.connection.get_user_index()
        self.assertEqual(response_data, default_response_data)

    # Token

    def testCreateToken(self):
        token = '123abc'
        self.connection.add_route('tokens/', 'POST',
                                  content={"token": "123abc"}, status_code=200)
        username = 'joe'
        password = 'J03'
        token_issued = self.connection.create_token(
            username=username, password=password)
        self.assertEqual(token_issued, token)
        self.assertEqual(self.connection.requests[0].auth, (username, password))

    # Data/Template/Run Tag Index

    def testGetDataTagIndex(self):
        self.connection.add_route('data-tags/', 'GET')
        response_data = self.connection.get_data_tag_index()
        self.assertEqual(response_data, default_response_data)

    def testGetTemplateTagIndex(self):
        self.connection.add_route('template-tags/', 'GET')
        response_data = self.connection.get_template_tag_index()
        self.assertEqual(response_data, default_response_data)

    def testGetRunTagIndex(self):
        self.connection.add_route('run-tags/', 'GET')
        response_data = self.connection.get_run_tag_index()
        self.assertEqual(response_data, default_response_data)

    # Data/Template/Run Label Index

    def testGetDataLabelIndex(self):
        self.connection.add_route('data-labels/', 'GET')
        response_data = self.connection.get_data_label_index()
        self.assertEqual(response_data, default_response_data)

    def testGetTemplateLabelIndex(self):
        self.connection.add_route('template-labels/', 'GET')
        response_data = self.connection.get_template_label_index()
        self.assertEqual(response_data, default_response_data)

    def testGetRunLabelIndex(self):
        self.connection.add_route('run-labels/', 'GET')
        response_data = self.connection.get_run_label_index()
        self.assertEqual(response_data, default_response_data)

    # Info/Version/Settings

    def testGetInfo(self):
        self.connection.add_route('info/', 'GET')
        response_data = self.connection.get_info()
        self.assertEqual(response_data, default_response_data)

    def testGetVersion(self):
        self.connection.add_route('info/', 'GET',
                                  content={"version":"123"}, status_code=200)
        version = self.connection.get_version()
        self.assertEqual(version, '123')

    def testGetStorageSettings(self):
        self.connection.add_route('storage-settings/', 'GET')
        response_data = self.connection.get_storage_settings()
        self.assertEqual(response_data, default_response_data)


if __name__ == '__main__':
    unittest.main()
