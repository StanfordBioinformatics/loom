Release Notes
=============

0.3.7
---------
* Retries for upload/download from Google Storage

0.3.6
---------
* Runs have "waiting" status until they start
* Runs are no longer changed to "killed" if they already completed
* Input/output detail routes on runs

0.3.5
---------
* Critical bugfix for 0.3.4

0.3.4
---------
* Pre-configure Kibana
* Disable X-Pack features in Kibana and Elasticsearch
* Handle several sporadic failures from gcloud services
* Handle gcloud gucket to bucket file copies longer than 30s
* Prune docker data volumes

0.3.3
----------
* Critical bugfix for 0.3.2 that prevented use on Google Cloud

0.3.2
----------
* Fluentd for logging, with kibana+elasticsearch for log viewing
* Nested templates by reference
* API documentation with swagger
* Reduced lag time in running tasks

0.3.1
----------
* Allow substitution in template output filenames
* Added LOOM_PRESERVE_ON_FAILURE and LOOM_PRESERVE_ALL flags for debugging
* Several bugfixes

0.3.0
-----------

* User-configurable playbooks
* Non-reverse-compatible simplifications to API
* Reduced server response times
* Dockerized deployment on local and google cloud
* Optional dockerized MySQL server
* Retry tasks if process stops responding

0.2.1
-----------

* Use release-specific DOCKER_TAG in default settings

0.2.0
-----------

* Loom can create a server locally or on Google Cloud Platform
* Accepts workflow templates in JSON or YAML format
* Web portal provides a brower interface for viewing templates, files, and runs
* Loom client for managing runs from the terminal
