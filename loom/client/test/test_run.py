#!/usr/bin/env python

import os
import unittest

from loom.client import run
from loom.client.run import InvalidConstantsException, MissingConstantsException


class TestRun(unittest.TestCase):

    workflow_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'testdata', 'workflow.yaml'))
    
    def test_init(self):
        parser = run.WorkflowRunner.get_parser()
        args = parser.parse_args(['--require_default_settings', '/dummyfile'])
        runner = run.WorkflowRunner(args)
        self.assertTrue(runner.args is not None)

    def test_validate_constants(self):
        ARGUMENT_SETS = [
            ['--no_save_settings', '--require_default_settings', '/dummyfile', 'constant1=value1', 'constant2=value2'], # Good constants
            ['--no_save_settings', '--require_default_settings', '/dummyfile'] # No constants
            ]

        for arg_set in ARGUMENT_SETS:
            self.get_workflow_runner(arg_set)

    def test_validate_constants_neg(self):
        ARGUMENT_SETS = [
            ['--no_save_settings', '--require_default_settings', '/dummyfile', '='], # No key
            ['--no_save_settings', '--require_default_settings', '/dummyfile', 'x=y=z'] # Too many values
            ]

        for arg_set in ARGUMENT_SETS:
            with self.assertRaises(InvalidConstantsException):
                self.get_workflow_runner(arg_set)

    def test_get_commandline_constants(self):
        runner = self.get_workflow_runner(['--no_save_settings', '--require_default_settings', '/dummyfile', 'constant1=value1', 'constant2=value2'])
        constants = runner._get_command_line_constants()
        self.assertEqual(constants['constant1'], 'value1')
        self.assertEqual(constants['constant2'], 'value2')        

    def test_read_workflow_file(self):
        runner = self.get_workflow_runner(['--no_save_settings', '--require_default_settings', self.workflow_file])
        runner._read_workflow_file()
        self.assertTrue('constants' in runner.workflow.keys())

    def test_substitute_commandline_constants(self):
        runner = self.get_workflow_runner(['--no_save_settings', '--require_default_settings', self.workflow_file, 'sampleid=123'])
        runner._read_workflow_file()
        runner._substitute_command_line_constants()
        self.assertEqual(runner.workflow['constants']['sampleid'], '123')

    def test_substitute_commandline_constants_neg(self):
        runner = self.get_workflow_runner(['--no_save_settings', '--require_default_settings', self.workflow_file])
        runner._read_workflow_file()
        with self.assertRaises(MissingConstantsException):
            runner._substitute_command_line_constants()

    def test_is_workflow_full_format(self):
        pass

    def get_workflow_runner(self, argument_set):
        return run.WorkflowRunner(args=self.get_args(argument_set))

    def get_args(self, argument_set):
        parser = run.WorkflowRunner.get_parser()
        return parser.parse_args(argument_set)

            
if __name__=='__main__':
    unittest.main()
