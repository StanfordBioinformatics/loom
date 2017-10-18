import unittest

from .. import connection

class MockResponse:

    status_code = 200

    def json(self):
        # Return mock data
        return {}


class MockConnection(connection.Connection):
    # Overrides connection.Connection methods that need a server
    # with mock methods

    def _get(self, relative_url, raise_for_status=True, params=None):
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

    def test_post_data_object(self):
        self.connection.post_data_object(self.data)
        self.assertEqual(self.connection.url, 'data-objects/')
        self.assertEqual(self.connection.method, 'POST')
        self.assertEqual(self.connection.data, self.data)


if __name__ == '__main__':
    unittest.main()
                
