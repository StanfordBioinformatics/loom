import loom
import os

def version():
    loomrootdir = os.path.dirname(loom.__file__)
    with open(os.path.join(loomrootdir,'VERSION')) as versionfile:
        return versionfile.read().strip()
