######################################
Server Settings
######################################

******************************
Passing settings to the client
******************************

If you start a Loom server without specifying any settings, Loom uses appropriate defaults for a local Loom server.

::
   
   loom server start

Non-default settings are assigned to a new server in one of three ways: using the ``--settings-file``/``-s`` flag to specify one or more config files:

::

   loom server start --settings-file mysettings.conf

or individually, using the ``--extra-settings``/``-e`` flag:

::

   loom server start --extra-settings LOOM_SERVER_NAME=MyServerName

or through environment variables that use the ``LOOM_`` prefix:

::

   export LOOM_SERVER_NAME=MyServerName
   loom server start

Multiple ``--settings-file`` flags are allowed, with the last file given highest priority for any conflicts. Multiple ``--extra-settings`` flags are also allowed. If different sources or settings are used together, the order of precedence, from highest to lowest, is:

1. environment variable
2. ``--extra-settings``
3. ``--settings-file``

********************
Settings file format
********************

Loom settings files are formatted like ini files, but without section headers. They are a flat file with a list of key-value pairs, separated by ":" or "=" and optional spaces. Comments are denoted with "#", and blank lines are allowed. For example:

*demosettings.conf:*

::

   LOOM_SERVER_NAME: loom-demo
   
   # Google cloud settings
   LOOM_MODE: gcloud
   LOOM_GCLOUD_SERVER_INSTANCE_TYPE: n1-standard-4
   LOOM_GCLOUD_WORKER_BOOT_DISK_SIZE_GB: 50

*********
Resources
*********

Some settings give the name of a file resource used by Loom. For example, LOOM_SSL_CERT_KEY_FILE and LOOM_SSL_CERT_FILE refer to the SSL key and certificate, and LOOM_GCE_PEM_FILE refers to the service account key file for Google Cloud Platform.

Rather than hard-code the path to these files, you must place them in one directory and make the setting indicate the file name or relative path in that directory. The directory is specified with the ``--resources`` flag on "loom server start".

*ssl-settings.conf* file contents:

::

   LOOM_SSL_CERT_KEY_FILE: loom.key
   LOOM_SSL_CERT_FILE: loom.crt

*resources/* directory contents:

::

   resources/loom.key
   resources/loom.crt

Use this command to start the server with the necessary files:

::

   loom server start --resource-dir ./resources --settings-file ssl-settings.conf 

On the client machine, Loom will cache a copy of these files in ~/.loom (or the value of the environment variable LOOM_SETTINGS_HOME), and it will create an additional copy on the server if it is remote, so the original copy does not need to be retained for the server to work.

*******************************************
Required settings to launch on Google Cloud
*******************************************

To launch a server on Google Cloud Platform, at a minimum you will need these required settings:

LOOM_MODE: gcloud
LOOM_GCE_PEM_FILE: your-gcp-key.json
LOOM_GCE_EMAIL: service-account-id@your-gcp-project.iam.gserviceaccount.com
LOOM_GCE_PROJECT: your-gcp-project
LOOM_GOOGLE_STORAGE_BUCKET: your-gcp-bucket

*****************
Updating settings
*****************

Not all settings can be changed safely. Changing LOOM_MYSQL_DATABASE, for example, will leave Loom unable to connect to the database.

However, sometimes it is necessary to modify settings, and many of them, such as LOOM_DEBUG, can be safely changed. You may want to test changes in a staging server before working with production data.

On the client machine:

1. Edit setting(s) in ~/.loom/server-settings.conf
2. Edit any resource files in ~/.loom/resources/
3. Wait for any runs in progress to complete.
4. loom server stop
5. loom server start

This will overwrite settings and resource files on the server with any changes you have made.

*****************
Modes
*****************

The LOOM_MODE setting is used to toggle between deployment modes. Currently loom has two modes: "local" and "gcloud". The default mode is "local".

*****************
Custom playbooks
*****************

The primary difference between modes is that they correspond to different sets of playbooks. You can find these in the Loom source code under "loomengine/client/playbooks/". Loom requires at least these five playbooks to be defined for any mode:

* {mode}_cleanup_task_attempt.yml
* {mode}_delete_server.yml
* {mode}_run_task_attempt.yml
* {mode}_start_server.yml
* {mode}_stop_server.yml

So for example, in the playbooks directory you will see a "gcloud_stop_server.yml" and a "local_stop_server.yml".

Loom allows you to use a custom set of playbooks to control how Loom is deployed. To do this, first create a copy of the "loomengine/client/playbooks" directory. Use the "local_*.yml" or "gcloud_*.yml" playbooks as a starting point. You may wish to change the prefix, but make sure that when you launch a new server, the LOOM_MODE setting matches the playbook prefix that you choose.

To pass the custom playbooks directory to loom when starting a new server, use the ``--playbooks`` flag:

::

   loom server start --my-custom-settings.conf --playbook-dir ./my-custom-playbooks

Loom settings are passed to the playbooks as environment variables. You are welcome to use your own settings for custom playbooks, but you may have to disable settings validation with "LOOM_SKIP_SETTINGS_VALIDATION=true".

*******************
Index of settings
*******************

----------------

================ ================
*default*        
*valid values*   
*notes*          
================ ================


Settings for all modes
**********************

LOOM_SERVER_NAME
----------------

================ ================
*default*        loom-server
*valid values*   String that begins with alpha, ends with alphanumeric, and contains only alphanumeric or -. Max length of 63.
================ ================

LOOM_SERVER_NAME determines how several components of the Loom server named. For example, the Docker container hosting the Loom server web application is named {{LOOM_SERVER_NAME}}-master, and the instance hosting the server in gcloud mode is named {{LOOM_SERVER_NAME}}.

LOOM_MODE
----------------

================ ================
*default*        local
*valid values*   local|gcloud|{custom}
================ ================

LOOM_MODE selects between different sets of playbooks. It also changes some default settings and the rules for settings validation. Supported modes are "local" and "gcloud". You may also develop custom playbooks that are compatible with another mode.

LOOM_DEBUG
----------------

================ ================
*default*        false
*valid values*   true|false
================ ================

When true, it activates several debugging tools and verbose server errors. Primarily for development use.

LOOM_LOG_LEVEL
----------------

================ ================
*default*        INFO
*valid values*   CRITICAL|ERROR|WARNING|INFO|DEBUG
================ ================

LOOM_DOCKER_IMAGE
-----------------

================ ================
*default*        loomengine/loom:{version}
================ ================

Docker image for server, worker, and scheduler

LOOM_DEFAULT_DOCKER_REGISTRY
----------------

================ ================
*default*        none
================ ================

LOOM_DEFAULT_DOCKER_REGISTRY applies to the LOOM_DOCKER_IMAGE and "docker_image" values in templates. Anywhere that a repo is given with no specific registry, LOOM_DEFAULT_DOCKER_REGISTRY will be assumed.

LOOM_STORAGE_TYPE
----------------

================ ================
*default*        local
*valid values*   local|google_storage
================ ================

Sets the type of persistent file storage. Usually google_storage would only be used with gcloud mode, but Loom does not impose this restriction. This may be useful for testing or for a custom deployment mode.

LOOM_STORAGE_ROOT
-----------------

================== ================
*default (local)*  ~/loomdata
*default (gcloud)* /loomdata
*valid values*     absolute file path
================== ================

LOOM_GOOGLE_STORAGE_BUCKET
--------------------------

================ ================
*default*        None. Setting is required if LOOM_STORAGE_TYPE==google_storage
*valid values*   Valid Google Storage bucket name.
================ ================

Loom will attempt to create the bucket it if it does not exist.

LOOM_ANSIBLE_INVENTORY
----------------------

================== ================
*default (local)*  localhost,
*default (gcloud)* gce_inventory_wrapper.py
*valid values*     Comma-delimited list of hosts, or executable filename
================== ================

Accepts either a comma-separated list of host inventory (e.g. "localhost," -- the comma is required) or a dynamic inventory executable. The executable must be in the playbooks directory.
 
LOOM_ANSIBLE_HOST_KEY_CHECKING
------------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

Leaving LOOM_ANSIBLE_HOST_KEY_CHECKING as false will ignore warnings about invalid host keys. These errors are common on Google Cloud Platform where IP addresses are frequently reused, causing conflicts with known_hosts.

LOOM_HTTP_PORT
--------------

================ ================
*default*        80
*valid values*   1–65535
================ ================

LOOM_HTTPS_PORT
---------------

================ ================
*default*        443
*valid values*   1–65535
================ ================

LOOM_HTTP_PORT_ENABLED
----------------------

================ ================
*default*        true
*valid values*   true|false
================ ================

LOOM_HTTPS_PORT_ENABLED
-----------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

LOOM_HTTP_REDIRECT_TO_HTTPS
---------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

If true, NGINX will redirect requests on LOOM_HTTP_PORT to LOOM_HTTPS_PORT.

LOOM_SSL_CERT_KEY_FILE
----------------------

================ ================
*default*        {{LOOM_SERVER_NAME}}+'-ssl-cert-key.pem'
================ ================

LOOM_SSL_CERT_FILE
------------------

================ ================
*default*        {{LOOM_SERVER_NAME}}+'-ssl-cert.pem'
================ ================

LOOM_SSL_CERT_CREATE_NEW
------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

If true, Loom will create a self-signed certificate and key. If LOOM_SSL_CERT_CREATE_NEW==false and LOOM_HTTPS_PORT_ENABLED==true, user must provide certificate and key in the resources directory and set LOOM_SSL_CERT_KEY_FILE and LOOM_SSL_CERT_FILE to the correct filenames.

LOOM_SSL_CERT_C
----------------

================ ================
*default*        US
================ ================

Used in subject field if self-signed SSL certificate if LOOM_SSL_CERT_CREATE_NEW==true.

LOOM_SSL_CERT_ST
----------------

================ ================
*default*        California
================ ================

Used in subject field if self-signed SSL certificate if LOOM_SSL_CERT_CREATE_NEW==true.

LOOM_SSL_CERT_L
----------------

================ ================
*default*        Palo Alto
================ ================

Used in subject field if self-signed SSL certificate if LOOM_SSL_CERT_CREATE_NEW==true.

LOOM_SSL_CERT_O
----------------

================ ================
*default*        Stanford University
================ ================

Used in subject field if self-signed SSL certificate if LOOM_SSL_CERT_CREATE_NEW==true.

LOOM_SSL_CERT_CN
----------------

================ ================
*default*        {{ansible_hostname}}
================ ================

Used in subject field if self-signed SSL certificate if LOOM_SSL_CERT_CREATE_NEW==true.

LOOM_MASTER_ALLOWED_HOSTS
-------------------------

================ ================
*default*        [*]
================ ================

List of hosts from which Loom will accept a connection. Corresponds to the django ALLOWED_HOSTS setting.

LOOM_MASTER_CORS_ORIGIN_ALLOW_ALL
---------------------------------

================ ================
*default*        false
================ ================

Whitelist all hosts for cross-origin resource sharing. Corresponds to the django CORS_ORIGIN_ALLOW_ALL setting.

LOOM_MASTER_CORS_ORIGIN_WHITELIST
---------------------------------

================ ================
*default*        []
================ ================

Hosts to be whitelisted for cross-origin resource sharing. Corresponds to the django CORS_ORIGIN_WHITELIST setting.

LOOM_TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS
------------------------------------------

================ ================
*default*        60
================ ================

Frequency of heatbeats sent by TaskAttempt monitor process to Loom server.

LOOM_TASKRUNNER_HEARTBEAT_TIMEOUT_SECONDS
-----------------------------------------

================ ================
*default*        300
================ ================

Kill any TaskAttempt that has not sent a heartbeat in this time.

LOOM_MAXIMUM_TASK_RETRIES
-------------------------

================ ================
*default*        2
================ ================

Maximum number of TaskAttempt retries.

LOOM_PRESERVE_ON_FAILURE
------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

Do not clean up instance or containers for any failed TaskAttempts. May be useful for debugging.

LOOM_PRESERVE_ALL
-----------------

================ ================
*default*        false
*valid values*   true|false
================ ================

Do not clean up instance or containers for any TaskAttempts. May be useful for debugging.

LOOM_MASTER_GUNICORN_WORKERS_COUNT
----------------------------------

================ ================
*default*        10
================ ================

LOOM_WORKER_CELERY_CONCURRENCY
------------------------------

================ ================
*default*        30
================ ================

LOOM_MYSQL_CREATE_DOCKER_CONTAINER
----------------------------------

================ ================
*default*        true
================ ================

Create a new Docker container to host the Loom database instead of connecting to an external database.

LOOM_MYSQL_HOST
----------------

================ ================
*default*        {{mysql_container_name}} if LOOM_MYSQL_CREATE_DOCKER_CONTAINER==true; otherwise no default.
================ ================

MySQL server connection settings.

LOOM_MYSQL_PORT
----------------

================ ================
*default*        3306
================ ================

MySQL server connection settings.

LOOM_MYSQL_USER
----------------

================ ================
*default*        loom
================ ================

MySQL server connection settings.

LOOM_MYSQL_PASSWORD
-------------------

================ ================
*default*        loompass
================ ================

MySQL server connection settings.

LOOM_MYSQL_DATABASE
-------------------

================ ================
*default*        loomdb
================ ================

MySQL server connection settings.

LOOM_MYSQL_IMAGE
----------------

================ ================
*default*        mysql:5.7.17
================ ================

Docker image used to create MySQL container if LOOM_MYSQL_CREATE_DOCKER_CONTAINER==true.

LOOM_MYSQL_RANDOM_ROOT_PASSWORD
-------------------------------

================ ================
*default*        true
================ ================

Create a random root password when initializing database if LOOM_MYSQL_CREATE_DOCKER_CONTAINER==true.

LOOM_MYSQL_SSL_CA_CERT_FILE
---------------------------

================ ================
*default*        none
================ ================

If needed, certificate files for MySQL database connection should be provided through the resources directory.

LOOM_MYSQL_SSL_CLIENT_CERT_FILE
-------------------------------

================ ================
*default*        none
================ ================

If needed, certificate files for MySQL database connection should be provided through the resources directory.

LOOM_MYSQL_SSL_CLIENT_KEY_FILE
------------------------------

================ ================
*default*        none
================ ================

If needed, certificate files for MySQL database connection should be provided through the resources directory.

LOOM_RABBITMQ_IMAGE
-------------------

================ ================
*default*        rabbitmq:3.6.8
================ ================

Docker image used to create RabbitMQ container.

LOOM_RABBITMQ_USER
----------------

================ ================
*default*        guest
================ ================

LOOM_RABBITMQ_PASSWORD
----------------

================ ================
*default*        guest
================ ================

LOOM_RABBITMQ_PORT
------------------

================ ================
*default*        5672
================ ================

LOOM_RABBITMQ_VHOST
-------------------

================ ================
*default*        /
================ ================

LOOM_NGINX_IMAGE
----------------

================ ================
*default*        nginx:1.11
================ ================

Docker image used to create NGINX container.

LOOM_NGINX_SERVER_NAME
----------------

================ ================
*default*        localhost
================ ================

Value for "server_name" field in NGINX configuration file.

LOOM_FLUENTD_IMAGE
------------------

================ ================
*default*        loomengine/fluentd-forest-googlecloud
================ ================

Docker image used to create fluentd container. The default repo includes fluentd with the forst and google-cloud plugins installed.

LOOM_FLUENTD_PORT
-----------------

================ ================
*default*        24224
================ ================

LOOM_FLUENTD_OUTPUTS
--------------------

================ ================
*default*        elasticsearch,file
*valid values*   comma-separated list of elasticsearch &| file &| gcloud_cloud
================ ================

LOOM_ELASTICSEARCH_IMAGE
------------------------

================ ================
*default*        docker.elastic.co/elasticsearch/elasticsearch:5.3.2
================ ================

Docker image used for elasticsearch container.

LOOM_ELASTICSEARCH_PORT
-----------------------

================ ================
*default*        9200
================ ================

LOOM_ELASTICSEARCH_JAVA_OPTS
----------------

================ ================
*default*        -Xms512m -Xmx512m
================ ================

LOOM_KIBANA_VERSION
-------------------

================ ================
*default*        5.3.2
================ ================

LOOM_KIBANA_IMAGE
-----------------

================ ================
*default*        docker.elastic.co/kibana/kibana:{{LOOM_KIBANA_VERSION}}
================ ================

Docker image to create Kibana container.

LOOM_KIBANA_PORT
----------------

================ ================
*default*        5601
================ ================

LOOM_FLOWER_INTERNAL_PORT
-------------------------

================ ================
*default*        5555
================ ================

LOOM_NOTIFICATION_ADDRESSES
---------------------------

================ ================
*default*        []
================ ================

Email addresses or http/https URLs to report to whenever a run reaches terminal status. Requires email configuration.

LOOM_DEFAULT_FROM_EMAIL
-----------------------

================ ================
*default*        
================ ================

Email configuration for notifications.

LOOM_EMAIL_HOST
---------------

================ ================
*default*        none
================ ================

Email configuration for notifications.

LOOM_EMAIL_PORT
---------------

================ ================
*default*        none
================ ================

Email configuration for notifications.

LOOM_EMAIL_HOST_USER
--------------------

================ ================
*default*        none
================ ================

Email configuration for notifications.

LOOM_EMAIL_HOST_PASSWORD
------------------------

================ ================
*default*        
================ ================

Email configuration for notifications.

LOOM_EMAIL_USE_TLS
------------------

================ ================
*default*        true
================ ================

Email configuration for notifications.

LOOM_EMAIL_USE_SSL
------------------

================ ================
*default*        true
================ ================

Email configuration for notifications.

LOOM_EMAIL_TIMEOUT
------------------

================ ================
*default*        0.0
================ ================

Email configuration for notifications.

LOOM_EMAIL_SSL_KEYFILE
----------------------

================ ================
*default*        
================ ================

Email configuration for notifications.

LOOM_EMAIL_SSL_CERTFILE
-----------------------

================ ================
*default*        
================ ================

Email configuration for notifications.

Settings for gcloud mode
************************

LOOM_GCE_PEM_FILE
-----------------

================ ================
*default*        none
*valid values*   filename
================ ================

This should be a JSON file with your Google Cloud Project service account key. File must be provided to Loom through the resources directory.

LOOM_GCE_PROJECT
----------------

================ ================
*default*        none
*valid values*   valid GCE project name
================ ================

LOOM_GCE_EMAIL
--------------

================ ================
*default*        none
*valid values*   valid GCE email identifier associated with the service account in LOOM_GCE_PEM_FILE
================ ================

LOOM_SSH_PRIVATE_KEY_NAME
-------------------------

================ ================
*default*        loom_id_rsa
*valid values*   valid filename string. Will create files in ~/.ssh/{{LOOM_SSH_PRIVATE_KEY_NAME}} and ~/.ssh/{{LOOM_SSH_PRIVATE_KEY_NAME}}.pub
================ ================

LOOM_GCLOUD_SERVER_BOOT_DISK_TYPE
---------------------------------

================ ================
*default*        pd-standard
*valid values*   valid GCP disk type
================ ================

LOOM_GCLOUD_SERVER_BOOT_DISK_SIZE_GB
------------------------------------

================ ================
*default*        10
*valid values*   float value in GB
================ ================

LOOM_GCLOUD_SERVER_INSTANCE_IMAGE
---------------------------------

================ ================
*default*        centos-7
*valid values*   valid GCP image
================ ================

LOOM_GCLOUD_SERVER_INSTANCE_TYPE
--------------------------------

================ ================
*default*        none
*valid values*   valid GCP instance type
================ ================

LOOM_GCLOUD_SERVER_NETWORK
--------------------------

================ ================
*default*        none
*valid values*   valid GCP network name
================ ================

LOOM_GCLOUD_SERVER_SUBNETWORK
-----------------------------

================ ================
*default*        none
*valid values*   valid GCP subnetwork name
================ ================

LOOM_GCLOUD_SERVER_ZONE
-----------------------

================ ================
*default*        us-central1-c
*valid values*   valid GCP zone
================ ================

LOOM_GCLOUD_SERVER_SKIP_INSTALLS
--------------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

If LOOM_GCLOUD_SERVER_SKIP_INSTALLS==true, when bringing up a server Loom will use the LOOM_GCLOUD_SERVER_INSTANCE_IMAGE directly without installing system packages. Before using this setting, you will need to create the base image. One way to do this is to start a Loom server with the defaults and then create an image from its disk.

Usually the same image can be used for both LOOM_GCLOUD_WORKER_INSTANCE_IMAGE and LOOM_GCLOUD_SERVER_INSTANCE_IMAGE.

LOOM_GCLOUD_SERVER_EXTERNAL_IP
------------------------------

================ ================
*default*        ephemeral
*valid values*   none|ephemeral|desired IP
================ ================

LOOM_GCLOUD_SERVER_TAGS
-----------------------

================ ================
*default*        none
*valid values*   comma-separated list of network tags
================ ================

LOOM_GCLOUD_WORKER_BOOT_DISK_TYPE
---------------------------------

================ ================
*default*        pd-standard
*valid values*   Valid GCP disk type
================ ================

LOOM_GCLOUD_WORKER_BOOT_DISK_SIZE_GB
------------------------------------

================ ================
*default*        10
*valid values*   float value in GB
================ ================

LOOM_GCLOUD_WORKER_SCRATCH_DISK_TYPE
------------------------------------

================ ================
*default*        
*valid values*   
================ ================

LOOM_GCLOUD_WORKER_SCRATCH_DISK_MIN_SIZE_GB
-------------------------------------------

================ ================
*default*        
*valid values*   
================ ================

LOOM_GCLOUD_WORKER_INSTANCE_IMAGE
---------------------------------

================ ================
*default*        centos-7
*valid values*   valid GCP image
================ ================

LOOM_GCLOUD_WORKER_INSTANCE_TYPE
--------------------------------

================ ================
*default*        none
*valid values*   valid GCP instance type
================ ================

LOOM_GCLOUD_WORKER_NETWORK
--------------------------

================ ================
*default*        none
*valid values*   valid GCP network name
================ ================

LOOM_GCLOUD_WORKER_SUBNETWORK
-----------------------------

================ ================
*default*        none
*valid values*   valid GCP subnetwork name
================ ================

LOOM_GCLOUD_WORKER_ZONE
-----------------------

================ ================
*default*        us-central1-c
*valid values*   valid GCP zone
================ ================

LOOM_GCLOUD_WORKER_SKIP_INSTALLS
--------------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

If LOOM_GCLOUD_WORKER_SKIP_INSTALLS==true, when bringing up a server Loom will use the LOOM_GCLOUD_WORKER_INSTANCE_IMAGE directly without installing system packages. Before using this setting, you will need to create the base image. One way to do this is to start a Loom server with the defaults and then create an image from its disk.

Usually the same image can be used for both LOOM_GCLOUD_WORKER_INSTANCE_IMAGE and LOOM_GCLOUD_SERVER_INSTANCE_IMAGE.

LOOM_GCLOUD_WORKER_EXTERNAL_IP
------------------------------

================ ================
*default*        ephemeral
*valid values*   none|ephemeral
================ ================

Note that using a reserved IP is not allowed, since multiple workers will be started. To restrict IP range, use a subnetwork instead.

LOOM_GCLOUD_WORKER_TAGS
-----------------------

================ ================
*default*        none
*valid values*   comma-separated list of network tags
================ ================

LOOM_GCLOUD_WORKER_USES_SERVER_INTERNAL_IP
------------------------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

If true, worker makes http/https connections to server using private IP.

LOOM_GCLOUD_CLIENT_USES_SERVER_INTERNAL_IP
------------------------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

If true, client makes ssh/http/https connections to server using private IP.

LOOM_GCLOUD_SERVER_USES_WORKER_INTERNAL_IP
------------------------------------------

================ ================
*default*        false
*valid values*   true|false
================ ================

If true, server makes ssh connections to worker using private IP.
