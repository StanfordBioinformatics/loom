Getting started
===============

This guide walks you through installing the Loom client onto a local machine. Once you have the client set up, you can use it to create a Loom server, either locally or in Google Cloud.

## Available branches

The GitHub branch or tag you choose should have a corresponding build in DockerHub, listed here: https://hub.docker.com/r/loomengine/loom/tags/

For now, we recommend the "development" branch for most users.

## Dependencies

* python >= 2.7 < 3.x
* [pip](http://pip.readthedocs.org/en/stable/installing/)
* [virtualenv](https://virtualenv.pypa.io/en/stable/) (use 'pip install virtualenv' to install)
* [Docker](https://www.docker.com/products/overview)
* gcc (Comes with XCode on Mac)
* MySQL
* git
* [Google Cloud SDK](https://cloud.google.com/sdk/) (for Google Cloud deployment only)

## Installing Loom from the development branch
```
unset PYTHONPATH        # because PYTHONPATH takes precedence over virtualenv
git clone -b development https://github.com/StanfordBioinformatics/loom.git
virtualenv loom-env
source loom-env/bin/activate
cd loom/
pip install -r requirements.txt
```

## Tests

Run tests to verify installation:

    loom test unit

## Starting a server

### Local

To start a local server with default settings:
```
loom server start --settings-file local.conf
```

### Google Cloud

Create a settings file that contains, minimally, the docker tag corresponding to branch that you are running.

_mysettings.ini:_
```
[gcloud]
DOCKER_TAG = development
```

Then run these commands in the shell:

    loom server set gcloud --name my-loom-server # name is optional
    loom server create --settings mysettings.ini
    loom server start

## Ubuntu setup of loom
<!--
    bash
    sudo apt-get install build-essential libssl-dev libffi-dev python-dev
    wget --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz
    tar -xf setuptools-1.4.2.tar.gz
    sudo python setuptools-1.4.2/setup.py install
    wget https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py
    sudo python get-pip.py
    sudo pip install virtualenv
-->
Note: Use Ubuntu 16.04 instead of 14.04, because Python 2.7.9 is not officially supported on 14.04, which leads to InsecurePlatformWarnings and headaches with SSL/TLS.

    sudo apt-get update
    sudo apt-get install -y build-essential libssl-dev libffi-dev libmysqlclient-dev python-dev git
    wget https://bootstrap.pypa.io/get-pip.py
    sudo -H python get-pip.py
    sudo -H pip install virtualenv

    # Then follow setup instructions above    

## CentOS installation of Loom client
```
# Add EPEL repo and update yum
sudo yum install -y epel-release
sudo yum update -y

# Install OS-level dependencies
sudo yum install -y gcc python-devel openssl-devel libffi-devel mysql-devel python-pip git

# Install and activate virtualenv
sudo pip install virtualenv
virtualenv loom-env
source loom-env/bin/activate

# Install google_compute_engine for gsutil
pip install google_compute_engine

# Then follow setup instructions above
```

## Production installation

Review the [Django deployment checklist](https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/).

## High-memory docker machine on mac

When running on a mac, the the docker machine uses a default memory size of 2024 MB for the VirtualBox. When you run out of memory, you will see "Killed" in the program output. If you need docker containers with higher memory, create it like this:

    docker-machine create -d virtualbox --virtualbox-memory 8192 highmem

Then you can load the necessary environment variables like this:

    eval "$(docker-machine env highmem)"

After this the docker client should be able to connect to the high memory machine. Launch the Loom server from a terminal where the highmem env settings are set.
