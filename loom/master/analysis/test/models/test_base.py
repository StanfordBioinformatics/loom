import copy

from django.test import TestCase
from analysis.models import Workflow
from . import fixtures

class TestBaseModel(TestCase):
    """Uses derived models to test functions on abstract base class.
    """

    def test_get_by_abbreviated_id(self):
        wf = Workflow.create(fixtures.flat_workflow_struct)
        id = wf._id
        short_id = id[0:7]
        wf_list = Workflow.get_by_abbreviated_id(short_id)
        self.assertEqual(wf_list.count(), 1)
        self.assertEqual(wf_list.first()._id, id)
        
    def test_get_by_name(self):
        wf = Workflow.create(fixtures.flat_workflow_struct)
        name = wf.name
        wf_list = Workflow.get_by_name(name)
        self.assertEqual(wf_list.count(), 1)
        self.assertEqual(wf_list.first()._id, wf._id)

    def test_get_by_name_or_id_using_name(self):
        wf = Workflow.create(fixtures.flat_workflow_struct)
        name = wf.name
        wf_list = Workflow.get_by_name_or_id(name)
        self.assertEqual(wf_list.count(), 1)
        self.assertEqual(wf_list.first()._id, wf._id)

    def test_get_by_name_or_id_using_id(self):
        wf = Workflow.create(fixtures.flat_workflow_struct)
        id = wf._id[0:7]
        wf_list = Workflow.get_by_name_or_id(id)
        self.assertEqual(wf_list.count(), 1)
        self.assertEqual(wf_list.first()._id, wf._id)

    def test_get_by_name_or_id_with_at(self):
        wf = Workflow.create(fixtures.flat_workflow_struct)
        id = '@'+wf._id[0:7]
        wf_list = Workflow.get_by_name_or_id(id)
        self.assertEqual(wf_list.count(), 1)
        self.assertEqual(wf_list.first()._id, wf._id)

    def test_get_by_name_or_id_where_name_matches_but_id_does_not(self):
        wf = Workflow.create(fixtures.flat_workflow_struct)
        name = wf.name
        id = '12345'
        wf_list = Workflow.get_by_name_or_id(name + '@' + id)
        self.assertEqual(wf_list.count(), 0)
        
    def test_get_by_name_or_id_where_both_match(self):
        wf1 = Workflow.create(fixtures.flat_workflow_struct)
        ambiguous_id = wf1._id[0:5]
        wf2_struct = copy.deepcopy(fixtures.flat_workflow_struct)
        wf2_struct['name'] = ambiguous_id
        wf2 = Workflow.create(wf2_struct)

        wf_list = Workflow.get_by_name_or_id(ambiguous_id)
        self.assertEqual(wf_list.count(), 2)
        self.assertEqual(wf_list[0]._id, wf1._id)
        self.assertEqual(wf_list[1]._id, wf2._id)
        
        
    def test_get_by_name_or_id_no_match(self):
        wf1 = Workflow.create(fixtures.flat_workflow_struct)
        wf_list = Workflow.get_by_name_or_id('nonsense')
        self.assertEqual(wf_list.count(), 0)
