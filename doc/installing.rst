###############
Getting started
###############

This guide walks you through installing the Loom client onto a local machine. Once you have the client set up, you can use it to create a Loom server, either locally or in Google Cloud. Then, we show you how to run a workflow on the newly-created server.

******************
Available branches
******************

The GitHub branch or tag you choose should have a corresponding build in DockerHub, listed here: https://hub.docker.com/r/loomengine/loom/tags/

For now, we recommend the "development" branch for most users.

*************
Prerequisites
*************

* python >= 2.7 < 3.x
* `pip <http://pip.readthedocs.org/en/stable/installing/>`_
* `virtualenv <https://virtualenv.pypa.io/en/stable/`_ (use 'pip install virtualenv' to install)
* `Docker <https://www.docker.com/products/overview>`_
* gcc (Comes with XCode on Mac)
* MySQL
* git
* `Google Cloud SDK <https://cloud.google.com/sdk/`_ (for Google Cloud deployment only)

*****************************************
Installing the development branch of Loom
*****************************************
::
    unset PYTHONPATH        # because PYTHONPATH takes precedence over virtualenv
    git clone -b development https://github.com/StanfordBioinformatics/loom.git
    virtualenv loom-env
    source loom-env/bin/activate
    cd loom/
    pip install -r requirements.txt

Tests
=====

Run tests to verify installation::

    sudo mkdir /var/log/loom
    sudo chmod a+w /var/log/loom
    loom test unit

Starting a server
=================

Local server
------------

To start a local server with default settings::

    loom server start --settings-file local.conf

Google Cloud server
-------------------

First, create a directory that will store files needed to administer the Loom server::

    mkdir ~/admin

Second, create a service account credential: https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys

Save the JSON credential to `~/admin/key.json`.

Third, make sure your Google Cloud SDK is initialized and authenticated::

    gcloud init

Fourth, copy the settings file template at `loom/loomengine/client/settings/gcloud.conf` and fill in values specific to your project. Make sure these settings are defined::

    LOOM_GCE_EMAIL:                 # service account email whose key you provided
    LOOM_GCE_PROJECT:
    LOOM_GOOGLE_STORAGE_BUCKET:

Save the config file as ~/gcloud.conf.

Finally, create and start the server::

    loom server start --settings-file ~/gcloud.conf --admin-files ~/admin

Making sure the server is running and reachable
===============================================
::
    loom server status

Running a workflow
==================

Once you have a server up and running, you can run a workflow!
::
    loom import file loom/doc/examples/hello_world/hello.txt
    loom import file loom/doc/examples/hello_world/world.txt
    loom import template loom/doc/examples/hello_world/hello_world.json
    loom run hello_world hello=hello.txt world=world.txt

Listing entities in Loom's database
===================================
::
    loom show files
    loom show templates
    loom show runs

Viewing run progress in a web browser
=====================================
::
    loom browser

Deleting the Loom server
========================
::
    loom server delete

****************
Additional notes
****************

Installing prerequisites on Ubuntu 16.04
========================================

Note: We recommend using Ubuntu 16.04 rather than 14.04, because Python 2.7.9 is not officially supported on 14.04. This leads to InsecurePlatformWarnings and headaches with SSL/TLS.

Install Docker: https://docs.docker.com/engine/installation/linux/ubuntu/
Add current user to docker group (may have to log out and back in for change to take effect): http://docs.oracle.com/cd/E52668_01/E75728/html/section_rdz_hmw_2q.html
::
    sudo apt-get update
    sudo apt-get install -y build-essential libssl-dev libffi-dev libmysqlclient-dev python-dev git
    wget https://bootstrap.pypa.io/get-pip.py
    sudo -H python get-pip.py
    sudo -H pip install virtualenv

    # Then follow Loom setup instructions above

Installing prerequisites on CentOS 7
====================================

Install Docker: https://docs.docker.com/engine/installation/linux/centos/
Add current user to docker group (may have to log out and back in for change to take effect): http://docs.oracle.com/cd/E52668_01/E75728/html/section_rdz_hmw_2q.html
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

Production installation
=======================

Review the `Django deployment checklist <https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/>`_

High-memory Docker containers on Mac OS
=======================================

When running on a Mac, docker-machine uses a default memory size of 2024 MB for VirtualBox. When you run out of memory, you will see "Killed" in the program output. If you need Docker containers with higher memory, create it like this::

    docker-machine create -d virtualbox --virtualbox-memory 8192 highmem

Then you can load the necessary environment variables like this::

    eval "$(docker-machine env highmem)"

After this the docker client should be able to connect to the high memory machine. Launch the Loom server from a terminal where the highmem env settings are set.
