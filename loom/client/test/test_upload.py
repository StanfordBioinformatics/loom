import os
import sys
import unittest

from loom.client.exceptions import *
from loom.client.upload import Uploader, WorkflowUploader, FileUploader
from loom.common.helper import get_null_logger
from loom.common.testserver import TestServer
from loom.master.loomdaemon import loom_daemon_logger

class TestUploadWorkflow(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()
        self.test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata')

    def tearDown(self):
        self.test_server.stop()

    def test_upload_with_prompt_inputs(self):
        """Upload a workflow that defines prompts instead of specific input values
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_prompt_inputs.json')])
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        # Verify ID assigned by server after upload
        self.assertEqual(workflow['_id'], 'a463c2f60fd63ee4d767ee266314287700b7684d2078465d5867b4d7893b8fa6')

    def test_upload_with_prompt_array_inputs(self):
        """Upload a workflow with array inputs that defines prompts instead of specific input values
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_prompt_array_inputs.json')])
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        # Verify ID assigned by server after upload
        self.assertEqual(workflow['_id'], '7a4d605a84d045ebf509df6adac91e55a5a717edb68dfea83ceaa776cb420eea')

    def test_upload_with_value_inputs(self):
        """Upload a workflow with specific input values assigned
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_value_inputs.json')])
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        # Verify ID assigned by server after upload
        self.assertEqual(workflow['_id'], 'cc4e6bedf024580bc378fc978cf3307d610f5894e09391174eddfcb689392a44')

    def test_upload_with_value_array_inputs(self):
        """Upload a workflow with array inputs and with specific input values assigned
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_value_array_inputs.json')])
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        # Verify ID assigned by server after upload
        self.assertEqual(workflow['_id'], '4fe754374534cdf1a3bf8561f8eb833f2936ebf4e509b5c3b65cd37b513a0a3f')

    def test_upload_with_value_file_inputs(self):
        """Upload a workflow with file inputs and with specific specific input values assigned
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_file_value_inputs.json')])

        # Raises error before file is uploaded
        with self.assertRaises(IdMatchedTooFewFileDataObjectsError):
            workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()

        # but not after file is uploaded
        file_args = parser.parse_args(['file', os.path.join(self.test_data_dir, 'hello.txt'), '--skip_source_record'])
        FileUploader(args=file_args, logger=get_null_logger()).run()
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()

        self.assertEqual(workflow['_id'], 'ec981e123e9a2ccceb7e0b27dd67303b3148b88223de1c8329b41649abb3ddfe')

    def test_upload_with_value_file_array_inputs(self):
        """Upload a workflow with file array inputs and with specific specific input values assigned
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_file_array_value_inputs.json')])

        # Raises error before file is uploaded
        with self.assertRaises(IdMatchedTooFewFileDataObjectsError):
            workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()

        # but not after file is uploaded
        file_args = parser.parse_args(['file', os.path.join(self.test_data_dir, 'hello.txt'), '--skip_source_record'])
        FileUploader(args=file_args, logger=get_null_logger()).run()
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()

    def test_upload_with_prompt_file_inputs(self):
        """Upload a workflow with file inputs and with prompts instead of specific input values
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_file_prompt_inputs.json')])
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        self.assertEqual(workflow['_id'], '21e5eaca65e6c735e0d76680846a22aed30982b9248f4e6992cfc855cef73808')

    def test_upload_with_prompt_file_array_inputs(self):
        """Upload a workflow with file array inputs and with prompts instead of specific input values
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_file_array_prompt_inputs.json')])
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        self.assertEqual(workflow['_id'], '9fff366f17c95ed2e88e1910e738453c412e7cc5e3563853e55e141b4b9fedfd')

    def test_expand_file_id(self):
        """Upload a workflow that references a file using a truncated input ID. Verify that the object created in the server uses
        the full ID
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_file_value_inputs.json')])
        file_args = parser.parse_args(['file', os.path.join(self.test_data_dir, 'hello.txt'), '--skip_source_record'])
        FileUploader(args=file_args, logger=get_null_logger()).run()
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        # File_ID should now have the full hash
        self.assertEqual(workflow['workflow_inputs'][0]['value'], 'hello.txt@e2971d1d4c307551e4ac6dfe3801838ee2d9537f505c3df459d2e756927dc609')

    def test_expand_file_array_ids(self):
        """Upload a workflow that files in a file array using a truncated input ID. Verify that the object created in the server uses
        the full IDs
        """
        parser = Uploader.get_parser()
        args = parser.parse_args(['workflow', os.path.join(self.test_data_dir, 'workflow_with_file_array_value_inputs.json')])
        file_args = parser.parse_args(['file', os.path.join(self.test_data_dir, 'hello.txt'), '--skip_source_record'])
        FileUploader(args=file_args, logger=get_null_logger()).run()
        workflow = WorkflowUploader(args=args, logger=get_null_logger()).run()
        # File_ID should now have the full hash
        self.assertEqual(workflow['workflow_inputs'][0]['value'][0], 'hello.txt@e2971d1d4c307551e4ac6dfe3801838ee2d9537f505c3df459d2e756927dc609')

class TestUploadFile(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()
        self.test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata')

    def tearDown(self):
        self.test_server.stop()

    def test_upload_file(self):
        parser = Uploader.get_parser()
        args = parser.parse_args(['file', os.path.join(self.test_data_dir, 'hello.txt'), '--skip_source_record'])
        file_obj = FileUploader(args=args, logger=get_null_logger()).run()
        self.assertEqual('e2971d1d4c307551e4ac6dfe3801838ee2d9537f505c3df459d2e756927dc609', file_obj[0]['_id'])


if __name__=='__main__':
    unittest.main()
