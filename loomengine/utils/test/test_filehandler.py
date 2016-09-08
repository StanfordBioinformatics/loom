#!/usr/bin/env python

import unittest
from loomengine.utils.filehandler import FileHandler

class TestFilehandler(unittest.TestCase):

    def testFilehandler(self):
        patterns = ['testdata/*.a', 'testdata/*.b']

if __name__=='__main__':
    unittest.main()
