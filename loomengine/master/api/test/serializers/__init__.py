from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

def get_mock_request():
    factory = APIRequestFactory()
    request = factory.get('/')
    return Request(request)

def get_mock_context():
    return {'request': get_mock_request()}
