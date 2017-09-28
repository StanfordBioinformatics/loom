import copy
from django.core.management.base import BaseCommand, CommandError
import uuid

from api.serializers import ExpandedDataNodeSerializer
from api.models import DataNode
from api.test.serializers import get_mock_context, get_mock_request

"""To test concurrent DataNode creation, run this command several times in the 
background. For example:

./manage.py verify_data_node_creation & ./manage.py verify_data_node_creation & ./manage.py verify_data_node_creation & ./manage.py verify_data_node_creation &
"""

class Command(BaseCommand):
    help = 'Make a big tree of DataNodes. Useful for testing concurrent write'

    def handle(self, *args, **options):
        self.create_and_verify_data_tree()

    def get_raw_data_integer_tree(self, breadth, depth, start=0):
        raw_data = []
        active_branches = [raw_data]
        for i in range(depth):
            new_active_branches = []
            for branch in active_branches:
                for j in range(breadth):
                    new_branch = []
                    branch.append(new_branch)
                    new_active_branches.append(new_branch)
            active_branches = new_active_branches
        i = 0
        for branch in active_branches:
            branch.append(i)
            i += 1
        return raw_data

    def compare_data(self, raw_data, saved_data):
        if isinstance(raw_data, list):
            if not isinstance(saved_data, list):
                raise Exception(
                    'Data mismatch. Printing raw, then saved: %s /// %s' % (
                        raw_data, saved_data))
            for raw, saved in zip(raw_data, saved_data):
                self.compare_data(raw, saved)
        else:
            if not str(raw_data) == saved_data['value']:
                raise Exception(
                    'Data mismatch. Printing raw, then saved: %s /// %s' % (
                        raw_data, saved_data))
            

    def create_and_verify_data_tree(self):
        id = uuid.uuid4()
        print "starting run %s with %s data nodes found" % (
            id, DataNode.objects.count())
        tree1_raw_data = self.get_raw_data_integer_tree(2, 2, start=0)
        s1 = ExpandedDataNodeSerializer(
            data={'contents': tree1_raw_data},
            context={'type': 'string',
                     'request': get_mock_request()})
        s1.is_valid(raise_exception=True)
        tree1 = s1.save()
        tree1_saved_data = ExpandedDataNodeSerializer(
            tree1, context=get_mock_context()).data
        if not str(tree1.uuid) == str(tree1_saved_data['uuid']):
            raise Exception(
                'UUID mismatch. Expected %s but found %s on saved model' % (
                    tree1.uuid, tree1_saved_data['uuid']))
        self.compare_data(tree1_raw_data, tree1_saved_data['contents'])
        print "ending run %s with %s data nodes found" % (
            id, DataNode.objects.count())
