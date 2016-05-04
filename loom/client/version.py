#!/usr/bin/env python
    
import argparse
import loom.common.version 

class Version:
    """Shows the Loom version."""

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):

        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        return parser

    def run(self):
        print loom.common.version.version()


if __name__=='__main__':
    response = Version().run()
