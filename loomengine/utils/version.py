import loomengine
import os

def version():
    loomengine.rootdir = os.path.dirname(loomengine.__file__)
    with open(os.path.join(loomengine.rootdir,'VERSION')) as versionfile:
        return versionfile.read().strip()
