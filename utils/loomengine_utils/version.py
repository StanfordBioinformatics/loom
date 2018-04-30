import os

def version():
    rootdir = os.path.dirname(__file__)
    with open(os.path.join(rootdir,'VERSION')) as versionfile:
        return versionfile.read().strip()
