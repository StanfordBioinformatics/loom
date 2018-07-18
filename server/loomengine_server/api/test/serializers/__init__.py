from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from api.models import DataNode
from api.serializers.runs import RunSerializer
def get_mock_request():
    factory = APIRequestFactory()
    request = factory.get('/')
    return Request(request)

def get_mock_context():
    return {'request': get_mock_request()}

def create_data_node_from_data_object(data_object):
    data_node = DataNode.objects.create(type=data_object.type)
    data_node.add_data_object([], data_object)
    return data_node

def create_run_from_template(template):
    s = RunSerializer(data={'template': '@%s' % template.uuid})
    s.is_valid(raise_exception=True)
    return s.save()
