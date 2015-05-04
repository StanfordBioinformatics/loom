from django.test import TestCase
from django.db import models
from django.core.exceptions import ValidationError 
import json
import hashlib

from apps.immutable.models import _Immutable
from apps.immutable.models import ChildModel
from apps.immutable.models import ParentModel


class TestParentChildImmutableObject(TestCase):
    list_child_json = '{"ChildModel":[{"field1":"fileid1","field2":"path1"},{"field1":"fileid2","field2":"path2"}]}'
    list_child2_json = '{"ChildModel":[{"field1":"newfile_id1","field2":"newfile_path1"},{"field1":"fileid2","field2":"path2"}]}'

    # test creating a object with a list of kids
    def test_create_list_child(self):
        model = ParentModel.create(self.list_child_json)
        self.assertIsNotNone(model._id) # parent created

        children = getattr(model, 'ChildModel')
        self.assertTrue(isinstance(children,list)) # if a list of children
        for child in children:
            self.assertIsNotNone(child._id)

    # test creating dup entry
    def test_create_dup_list_child(self):
        model = ParentModel.create(self.list_child_json)
        model2 = ParentModel.create(self.list_child_json) # a dup entry will cause complain

    # if the child updated 
    def test_updated_list_child(self):
        model = ParentModel.create_no_save(self.list_child_json)
        model2 = ParentModel.create_no_save(self.list_child2_json)
        # model and model2 still have the same _id?
        self.assertNotEqual(model._calculate_unique_id(), model2._calculate_unique_id() )


    ##### code [testing dict children] started here #####
    dict_child_json = '{"ChildModel":{"field1":"step1","field2":"file1"}}'
    dict_child2_json = '{"ChildModel":{"field1":"newstep1","field2":"file1"}}'
    # test creating a object with a dict of kids
    def test_create_dict_child(self):
        model = ParentModel.create(self.dict_child_json)
        self.assertIsNotNone(model._id)

        children = getattr(model, 'ChildModel')
        self.assertTrue(isinstance(children,dict)) # if a list of children
        for child in children:
            self.assertIsNotNone(children[child]._id)
    
    # test creating dup entry
    def test_create_dup_dict_child(self):
        model = ParentModel.create(self.dict_child_json)
        model2 = ParentModel.create(self.dict_child_json) #a dup entry will cause complain

    # if the child updated 
    def test_updated_dict_child(self):
        model = ParentModel.create_no_save(self.dict_child_json)
        model2 = ParentModel.create_no_save(self.dict_child2_json)
        # model and model2 still have the same _id?
        self.assertNotEqual(model._calculate_unique_id , model2._calculate_unique_id() )
    

