.. _getting-started:

###############
Getting Started
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
* `Docker <https://docs.docker.com/engine/installation/>`_ (required in default 'local' mode)
* `Google Cloud SDK <https://cloud.google.com/sdk/>`_ (required in 'gcloud' mode)

Installing
==========

To install the client, use::

  pip install loomengine

You do not need to install the loomengine_worker or loomengine_server packages directly. The client can provision a server, and the server can provision workers, either in local docker containers or on newly provisioned VMs.

Tests
=====

Run tests to verify installation::

    loom test unit

Starting a server
=================

Local server
------------
To start a local server with default settings::

    loom server start

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
    gcloud auth application-default

Fourth, copy the settings file template from "loom/loomengine/client/settings/gcloud.conf" to "~/loom-gcloud.conf" and fill in values specific to your project in the copied version. Make sure these settings are defined::

    LOOM_GCE_EMAIL:                 # service account email whose key you provided
    LOOM_GCE_PEM_FILE: key.json
    LOOM_GCE_PROJECT:
    LOOM_GOOGLE_STORAGE_BUCKET:

Finally, create and start the server::

    loom server start --settings-file ~/loom-gcloud.conf --admin-files-dir ~/loom-admin-files

Verify that the server is running
---------------------------------
::

    loom server status

Running a workflow
==================

Export an example workflow
--------------------------

Loom ships with example workflows that demonstrate the features of Loom workflow definitions give instructions on how to run a workflow.

To see a list of available examples, use:

::

   loom example list

To work with an example, export it by name:

::

   loom example export hello_world

This will create a local directory with the example, any input files, and a README.rst file explaining the example and how to execute it.

Import the template and input files
--------------------------------------------

::

    loom file import hello_world/hello.txt
    loom file import hello_world/world.txt
    loom template import hello_world/hello_world.yaml

Start a run
-----------
::

    loom run start hello_world hello=hello.txt world=world.txt

Listing objects in Loom's database
==================================
::

    loom file list
    loom template list
    loom run list

Using unique identifiers and hash values
========================================

Note that a unique identifier (a UUID) has been appended to the file, template, and run names, predeeded by the "@" symbol. If you have multiple objects with the same name, it is good practice to use all or part of the UUID along with the human readable name, e.g.

::

    loom run start hello_world@37fa721e hello=hello.txt@17c73d43 world=world.txt@f2fc4af5

(UUIDs are generated randomly at the time of import, so yours will not match those shown in the command above.)
    
You can also use hash of the file contents to uniquely identify imported data files or templates. Hashes are preceeded with the "$" symbol.

::

   loom run start hello_world\$11405cbf2599f017c67179c271a064ec hello=hello.txt\$b1946ac92492d2347c6235b4d2611184 world=world.txt\$591785b794601e212b260e25925636fd

Human-readable names are optional when another identifier is used, but including them will improve readability.

Viewing run progress in a web browser
=====================================
::

    loom browser

Deleting the Loom server
========================
Warning! This may result in permanent loss of data.
::

    loom server delete

You will be prompted to confirm the server name in order to delete (default "loom-server")
