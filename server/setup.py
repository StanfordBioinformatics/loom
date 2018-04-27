"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

def _get_version():
    versionpath = path.join(here, 'loomengine_server', 'VERSION')
    with open(versionpath) as versionfile:
        return versionfile.read().strip()
version = _get_version()


setup(
    name='loomengine_server',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    description='loom workflow engine (server)',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/StanfordBioinformatics/loom',

    # Could use a utility like Travis CI to automatically create pip releases from GitHub tags.
    #download_url='https://github.com/StanfordBioinformatics/loom/tarball/'+version,

    # Author details
    author='Nathan Hammond, Isaac Liao',
    author_email='info@loomengine.org',
    maintainer='Nathan Hammond',
    maintainer_email='info@loomengine.org',

    # Choose your license
    license='GNU Affero GPL',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: System :: Distributed Computing',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords='bioinformatics pipeline runner workflow engine job scheduler',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=[]),
    include_package_data=True,

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    # py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'ansible==2.3.1.0',
        'apache-libcloud==1.5.0',
        'celery==4.0.2',
        'Django==1.11',
        'django-celery-results==1.0.1',
        'django-cors-headers==2.0.2',
        'django-debug-toolbar==1.7',
        'django-extensions==1.7.8',
        'django-mptt==0.8.7',
        'djangorestframework==3.6.2',
        'django-rest-swagger==2.1.2',
        'docker-py==1.10.6',                 # used by Ansible to run Docker modules and Loom server to run NGINX container
        'eventlet==0.21.0',
        'flower==0.9.1',
        'google-api-python-client==1.6.2',
        'google-apitools>=0.5.8',
        'google-cloud==0.26.1',
        'gunicorn>=19.7.1',
        'Jinja2==2.9.6',
        'jsonfield==2.0.1',
        'jsonschema==2.6.0',
        'MySQL-python==1.2.5',
        'oauth2client==3.0.0',
        'python-dateutil==2.6.0',
        'PyYAML==3.12',
        'requests==2.13.0',            # match docker-py dependency
        'SQLAlchemy==1.1.9',
        'loomengine_utils==%s' % version,
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # package_data={
    #     'sample': ['package_data.dat'],
    # },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
         'console_scripts': [
             'loom-manage=loomengine_server.manage:main',
         ],
     },
)
