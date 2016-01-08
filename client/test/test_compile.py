#!/usr/bin/env python

import os
import sys
import time
import unittest

from loom.client import loom_compile


class TestLoomCompile(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_step_files_to_ports(self):
        obj = {"workflows": [
            {"steps": [
                {
                    "name": "my_awesome_step",
                    "input_files": ["input_file", "better_input_file"],
                    "output_files": ["best_output_file", "bestest_output_file"]
                }
            ]}
        ]}
        loom_compile.step_files_to_ports(obj)
        self.assertIn("workflows", obj)
        self.assertIn("steps", obj['workflows'][0])
        self.assertIn("input_ports", obj['workflows'][0]['steps'][0])
        self.assertIn("output_ports", obj['workflows'][0]['steps'][0])
        self.assertNotIn("input_files", obj['workflows'][0]['steps'][0])
        self.assertNotIn("output_files", obj['workflows'][0]['steps'][0])
        self.assertIn("name", obj['workflows'][0]['steps'][0]['input_ports'][0])
        self.assertIn("file_name", obj['workflows'][0]['steps'][0]['input_ports'][0])
        self.assertIn("name", obj['workflows'][0]['steps'][0]['output_ports'][0])
        self.assertIn("file_name", obj['workflows'][0]['steps'][0]['output_ports'][0])
        self.assertIn("name", obj['workflows'][0]['steps'][0]['input_ports'][1])
        self.assertIn("file_name", obj['workflows'][0]['steps'][0]['input_ports'][1])
        self.assertIn("name", obj['workflows'][0]['steps'][0]['output_ports'][1])
        self.assertIn("file_name", obj['workflows'][0]['steps'][0]['output_ports'][1])
        self.assertEqual("input_file", obj['workflows'][0]['steps'][0]['input_ports'][0]['file_name'])
        self.assertEqual("my_awesome_step_input_file_in", obj['workflows'][0]['steps'][0]['input_ports'][0]['name'])
        self.assertEqual("best_output_file", obj['workflows'][0]['steps'][0]['output_ports'][0]['file_name'])
        self.assertEqual("my_awesome_step_best_output_file_out", obj['workflows'][0]['steps'][0]['output_ports'][0]['name'])

    def test_add_data_pipes(self):
        obj = {"workflows": [
            {"steps": [
                {
                    "name": "animate_image",
                    "input_ports": [{"name": "inputport1", "file_name": "cats.png"}],
                    "output_ports": [{"name": "outputport1", "file_name": "cats.gif"}],
                },
                {
                    "name": "render_movie",
                    "input_ports": [{"name": "inputport1", "file_name": "cats.gif"}],
                    "output_ports": [{"name": "outputport1", "file_name": "cats.mpg"}],
                }
            ]}
        ]}
        loom_compile.add_data_pipes(obj)
        self.assertIn("workflows", obj)
        self.assertIn("data_pipes", obj['workflows'][0])
        self.assertIn("source", obj['workflows'][0]['data_pipes'][0])
        self.assertIn("destination", obj['workflows'][0]['data_pipes'][0])
        self.assertIn("step", obj['workflows'][0]['data_pipes'][0]['source'])
        self.assertIn("port", obj['workflows'][0]['data_pipes'][0]['source'])
        self.assertIn("step", obj['workflows'][0]['data_pipes'][0]['destination'])
        self.assertIn("port", obj['workflows'][0]['data_pipes'][0]['destination'])
        self.assertEqual("animate_image", obj['workflows'][0]['data_pipes'][0]['source']['step'])
        self.assertEqual("outputport1", obj['workflows'][0]['data_pipes'][0]['source']['port'])
        self.assertEqual("render_movie", obj['workflows'][0]['data_pipes'][0]['destination']['step'])
        self.assertEqual("inputport1", obj['workflows'][0]['data_pipes'][0]['destination']['port'])

if __name__=='__main__':
    unittest.main()
