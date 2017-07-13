.. _getting-started:

###############
Getting started
###############

This guide walks you through installing the Loom client, using it to launch a Loom server either on your local machine or on Google Cloud Platform, and running a workflow.

********************************************
Installing the Loom client
********************************************

Prerequisites
=============

Required
--------
* python >= 2.7 < 3.x
* `pip <http://pip.readthedocs.org/en/stable/installing/>`_
* `Docker <https://www.docker.com/products/overview>`_
* gcc (Comes with XCode on Mac)
* MySQL

Optional
--------
* `git <https://git-scm.com/downloads>`_
* `virtualenv <https://virtualenv.pypa.io/en/stable/>`_ (use 'pip install virtualenv' to install)
* `Google Cloud SDK <https://cloud.google.com/sdk/>`_ (for Google Cloud deployment only)

Releases
========

You can see all available releases here: https://github.com/StanfordBioinformatics/loom/releases. 

If cloning from github, the `master branch <https://github.com/StanfordBioinformatics/loom/tree/master>`_ contains the latest stable release.

Download the source code
========================
You can download and extract Loom as a \*.tar.gz or \*.zip file from the `Loom releases page <https://github.com/StanfordBioinformatics/loom/releases>`_.

Alternatively, you can clone the Loom repository using git::

    git clone https://github.com/StanfordBioinformatics/loom.git

Virtualenv setup (recommended)
==============================
Create an isolated python environment for Loom using virtualenv. This creates a folder called "loom-env" in your current directory. This can be done anywhere convenient, e.g. inside the Loom root directory.

::

    unset PYTHONPATH
    virtualenv loom-env
    source loom-env/bin/activate

Refer to the virtualenv `user guide <https://virtualenv.pypa.io/en/stable/userguide/>`_ for instructions on activating and deactivating the environment.
    
Install Loom
============
Change directories to the loom root directory where the "LICENSE" file is located and run this command to install Loom and its dependencies::

    pip install -r requirements.txt

Tests
=====

Run tests to verify installation::

    loom test unit

Starting a server
=================

Local server
------------
To start a local server with default settings::

    loom server start --settings-file local.conf

Skip to "Running a workflow" to run an analysis on the local server.

Google Cloud server
-------------------

SECURITY WARNING: Running on Google Cloud is not currently secure with default firewall settings. By default, the Loom server accepts requests on port 443 from any source. Unless you restrict access, anyone in the world can access data or cause jobs to be run with your service account key. At present, Loom should only be run in Google Cloud if it is in a secured private network.

Unless you have read and understand the warning above, do not proceed with the instructions below.

First, create a directory that will store files needed to administer the Loom server::

    mkdir ~/loom-admin-files

Second, create a service account credential. Refer to the `instructions <https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys>`_ in Google Cloud documentation.


Save the JSON credential to "~/loom-admin-files/key.json".

Third, make sure your Google Cloud SDK is initialized and authenticated::

    gcloud init
    gcloud auth application-defaul

Fourth, copy the settings file template from "loom/loomengine/client/settings/gcloud.conf" to "~/loom-gcloud.conf" and fill in values specific to your project in the copied version. Make sure these settings are defined::

    LOOM_GCE_EMAIL:                 # service account email whose key you provided
    LOOM_GCE_PEM_FILE: key.json
    LOOM_GCE_PROJECT:
    LOOM_GOOGLE_STORAGE_BUCKET:

Finally, create and start the server::

    loom server start --settings-file ~/loom-gcloud.conf --admin-files-dir ~/loom-admin-files

Running a workflow
==================

Verify that the server is running
---------------------------------
::

    loom server status

Import the workflow template and input files
--------------------------------------------
::

    loom import file loom/doc/examples/hello_world/hello.txt
    loom import file loom/doc/examples/hello_world/world.txt
    loom import template loom/doc/examples/hello_world/hello_world.json

Start a workflow run
--------------------
::

    loom run hello_world hello=hello.txt world=world.txt

Listing entities in Loom's database
===================================
::

    loom show files
    loom show templates
    loom show runs

Using unique identifiers
========================

Note that a unique identifier (a UUID) has been appended to the file, template, and run names. If you have multiple objects with the same name, it is good practice to use all or part of the UUID along with the human 
readable name, e.g.
::

    loom run hello_world@37fa721e hello=hello.txt@17c73d43 world=world.txt@f2fc4af5

Viewing run progress in a web browser
=====================================
::

    loom browser

Deleting the Loom server
========================
Warning! This may result in permanent loss of data.
::

    loom server delete

You will be prompted to confirm the server name in order to delete (default "loom-local" or "loom-gcloud")

****************
Additional notes
****************

Installing prerequisites on Ubuntu 16.04
========================================

Note: We recommend using Ubuntu 16.04 rather than 14.04, because Python 2.7.9 is not officially supported on 14.04. This leads to InsecurePlatformWarnings and headaches with SSL/TLS.

* Install Docker: https://docs.docker.com/engine/installation/linux/ubuntu/
* Add current user to docker group (may have to log out and back in for change to take effect): http://docs.oracle.com/cd/E52668_01/E75728/html/section_rdz_hmw_2q.html

::

    sudo apt-get update
    sudo apt-get install -y build-essential libssl-dev libffi-dev libmysqlclient-dev python-dev git
    wget https://bootstrap.pypa.io/get-pip.py
    sudo -H python get-pip.py
    sudo -H pip install virtualenv

    # Then follow Loom setup instructions above

Installing prerequisites on CentOS 7
====================================

* Install Docker: https://docs.docker.com/engine/installation/linux/centos/
* Add current user to docker group (may have to log out and back in for change to take effect): http://docs.oracle.com/cd/E52668_01/E75728/html/section_rdz_hmw_2q.html

::

    # Add EPEL repo and update yum
    sudo yum install -y epel-release
    sudo yum update -y

    # Install OS-level dependencies
    sudo yum install -y gcc python-devel openssl-devel libffi-devel mysql-devel python-pip git

    # Install and activate virtualenv
    sudo pip install virtualenv

    # Then follow Loom setup instructions above, but after activating virtualenv, add the selinux package:
    cp -r /usr/lib64/python2.7/site-packages/selinux $VIRTUAL_ENV/lib/python2.7/site-packages
