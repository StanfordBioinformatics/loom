#############
Release Notes
#############

0.5.0
=============
* Tags and labels for files, templates, and runs
* Changed client commands to follow 'loom {noun} {verb}' pattern

0.4.1
=============
* Notification for completed runs by email or posting JSON to URL
* Documentation for Loom templates
* Templates can be referenced by hash
* Added retries to file import/export, docker pull, other external services
* Added "--original-copy" option to "loom file import"
* Added LOOM_DEFAULT_DOCKER_REGISTRY setting

0.4.0
=============
* Parallel workflows
* Deprecated fixed inputs, replaced with optional and overridable "data" field on standard inputs
* User-defined run names, using the optional "--name" flag with "loom run"
* Updated examples, including two parallel examples "word_scoring" and "word_combinations"
* Saving of templates is no longer asynchronous, so any errors are raised immediately with "loom import template"
* Outputs can now use "glob" source in addition to "filename" and "stream"

0.3.8
=============
* Run overview shows nested runs, tasks, and task-attempts

0.3.7
=============
* Retries for upload/download from Google Storage

0.3.6
=============
* Runs have "waiting" status until they start
* Runs are no longer changed to "killed" if they already completed
* Input/output detail routes on runs

0.3.5
=============
* Critical bugfix for 0.3.4

0.3.4
=============
* Pre-configure Kibana
* Disable X-Pack features in Kibana and Elasticsearch
* Handle several sporadic failures from gcloud services
* Handle gcloud gucket to bucket file copies longer than 30s
* Prune docker data volumes

0.3.3
=============
* Critical bugfix for 0.3.2 that prevented use on Google Cloud

0.3.2
=============
* Fluentd for logging, with kibana+elasticsearch for log viewing
* Nested templates by reference
* API documentation with swagger
* Reduced lag time in running tasks

0.3.1
=============
* Allow substitution in template output filenames
* Added LOOM_PRESERVE_ON_FAILURE and LOOM_PRESERVE_ALL flags for debugging
* Several bugfixes

0.3.0
=============
* User-configurable playbooks
* Non-reverse-compatible simplifications to API
* Reduced server response times
* Dockerized deployment on local and google cloud
* Optional dockerized MySQL server
* Retry tasks if process stops responding

0.2.1
=============
* Use release-specific DOCKER_TAG in default settings

0.2.0
=============
* Loom can create a server locally or on Google Cloud Platform
* Accepts workflow templates in JSON or YAML format
* Web portal provides a brower interface for viewing templates, files, and runs
* Loom client for managing runs from the terminal
