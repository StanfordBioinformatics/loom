import unittest

from loomengine.utils import connection

class MockResponse:

    def json(self):
        # Return mock data
        return {}


class MockConnection(connection.Connection):

    def _get(self, relative_url):
        self.method = 'GET'
        self.url = relative_url
        return MockResponse()

    def _post(self, data, relative_url):
        self.method = 'POST'
        self.data = data
        self.url = relative_url
        return MockResponse()

    def _put(self, data, relative_url):
        self.method = 'PUT'
        self.data = data
        self.url = relative_url
        return MockResponse()

    def _patch(self, data, relative_url):
        self.method = 'PATCH'
        self.data = data
        self.url = relative_url
        return MockResponse()


class TestConnection(unittest.TestCase):

    data = {'mock', 'data'}

    def setUp(self):
        self.connection = MockConnection('root_url')

    def test_post_file_data_object(self):
        self.connection.post_file_data_object(self.data)
        self.assertEqual(self.connection.url, 'files/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.data)

    def test_update_worker_processes(self):
        worker_process_id = 10
        self.connection.update_worker_process(worker_process_id, self.data)
        self.assertEqual(self.connection.url, 'worker-processes/%s/' % worker_process_id)
        self.assertEqual(self.connection.method, 'PATCH')
        self.assertEqual(self.connection.data, self.data)


if __name__ == '__main__':
    unittest.main()
                
