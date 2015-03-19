#!/usr/bin/env python

class XppfClient:

    def __init__(self, opts=None):
        if not opts:
            opts=self.get_opts()

    def get_opts(self):
        from argparse import ArgumentParser
        

if __name__=='__main__':
    XppfClient()
