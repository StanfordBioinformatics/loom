#!/usr/bin/env python

import argparse
import copy
from datetime import datetime
import docker
import errno
import json
import logging
import os
import requests
import string
import subprocess
import sys
import time
import uuid

import loomengine.utils
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection
from loomengine.utils.connection import TASK_RUN_ATTEMPT_STATUSES as STATUS
from loomengine.utils.logger import StreamToLogger


class ContainerStartError(Exception):
    pass

class ContainerPullError(Exception):
    pass

class TaskRunAttemptNotFoundError(Exception):
    pass

class DockerDaemonNotFoundError(Exception):
    pass

class FileImportError(Exception):
    pass


class TaskRunner(object):

    DOCKER_SOCKET = 'unix://var/run/docker.sock'
    HEARTBEAT_INTERVAL_SECONDS = 60
    LOOM_RUN_SCRIPT_NAME = 'loom_run_script'

    def __init__(self, args=None, mock_connection=None, mock_filemanager=None):
        if args is None:
            args = self._get_args()
        self.settings = {
            'TASK_RUN_ATTEMPT_ID': args.run_attempt_id,
            'MASTER_URL': args.master_url,
            'LOG_LEVEL': args.log_level,
            'LOG_FILE': args.log_file,
        }

        # Errors here can't be report since there is no server connection
        # or logger
        self._init_loggers()

        # Errors here can be logged but not reported to server
        if mock_connection is not None:
            self.connection = mock_connection
        else:
            try:
                self.connection = Connection(self.settings['MASTER_URL'])
            except Exception as e:
                self.logger.error('Failed to initialize server connection: "%s"' % str(e))
                raise e

        # Errors here can be both logged and reported to server
        try:
            self._set_status(STATUS.INITIALIZING_MONITOR)
            self._init_task_run_attempt()
            if mock_filemanager is not None:
                self.filemanager = mock_filemanager
            else:
                self.filemanager = FileManager(self.settings['MASTER_URL'])
            self.settings.update(self._get_worker_settings())
            self._init_docker_client()
            self._init_working_dir()
        except Exception as e:
            try:
                self._report_error(message='Failed to initialize', detail=str(e))
                self._set_status(STATUS.FINISHED)
            except:
                # Raise original error, not status change error
                pass
            raise e

    def _init_loggers(self):
        self.logger = logging.getLogger(__name__)
        self.utils_logger = logging.getLogger(loomengine.utils.__name__)

        LEVELS = {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
        }
        log_level = LEVELS[self.settings['LOG_LEVEL']]
        self.logger.setLevel(log_level)
        self.utils_logger.setLevel(log_level)
        if log_level != 'DEBUG':
            self.logger.raiseExceptions = False
            self.utils_logger.raiseExceptions = False

        if self.settings['LOG_FILE'] is None:
            self._init_logger_stdout_handler()
        else:
            self._init_logger_file_handler()

    def _init_logger_stdout_handler(self):
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.utils_logger.addHandler(logging.StreamHandler(sys.stdout))

    def _init_logger_file_handler(self):
        self._init_directory(os.path.dirname(self.settings['LOG_FILE']))
        file_handler = logging.FileHandler(self.settings['LOG_FILE'])
        file_handler.setFormatter(
            logging.Formatter('%(levelname)s [%(asctime)s] %(message)s'))
        self.logger.addHandler(file_handler)
        self.utils_logger.addHandler(file_handler)

        # Route stdout and stderr to logger
        stdout_logger = StreamToLogger(self.logger, logging.INFO)
        sys.stdout = stdout_logger
        stderr_logger = StreamToLogger(self.logger, logging.ERROR)
        sys.stderr = stderr_logger

    def _init_directory(self, directory, new=False):
        if new and os.path.exists(directory):
            raise Exception('Directory %s already exists' % directory)
        if os.path.exists(directory) and not os.path.isdir(directory):
            raise Exception('Cannot initialize directory %s since a file exists with that name' % directory)
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError as e:
            raise Exception('Failed to create directory %s. %s' % (directory, e.strerror))

    def _init_task_run_attempt(self):
        self.task_run_attempt = self.connection.get_task_run_attempt(self.settings['TASK_RUN_ATTEMPT_ID'])
        if self.task_run_attempt is None:
            raise TaskRunAttemptNotFoundError('TaskRunAttempt ID "%s" not found' % self.settings['TASK_RUN_ATTEMPT_ID'])

    def _get_worker_settings(self):
        settings = self.connection.get_worker_settings(self.settings['TASK_RUN_ATTEMPT_ID'])
        if settings is None:
            raise WorkerSettingsError('Worker settings not found')
        return settings

    def _init_docker_client(self):
        self.docker_client = docker.Client(base_url=self.DOCKER_SOCKET)
        self._verify_docker()

    def _verify_docker(self):
        try:
            self.docker_client.info()
        except requests.exceptions.ConnectionError:
            raise DockerDaemonNotFoundError('Failed to connect to Docker daemon')

    def _init_working_dir(self):
        self.logger.info('Initializing working directory %s' % self.settings['WORKING_DIR'])
        self._init_directory(self.settings['WORKING_DIR'], new=True)

    def run(self):
        try:
            self._try_to_copy_inputs()
            self._try_to_create_run_script()
            self._try_to_pull_image()
            self._try_to_create_container()
            self._try_to_run_container()
            self._try_to_get_returncode()
        except Exception as e:
            self.logger.error('Exiting run with error: %s' % str(e))
            raise e

    def cleanup(self):
        # Never raise errors, so cleanup can continue
        self._set_status(STATUS.SAVING_OUTPUTS)

        self._try_to_save_process_logs()
            

        try:
            self._try_to_save_outputs()
        except Exception as e:
            self._report_error(message='Failed to save outputs', detail=str(e))

        try:
            self._try_to_save_monitor_log()
        except Exception as e:
            self._report_error(message='Failed to save monitor log', detail=str(e))

        self._set_status(STATUS.FINISHED)
        self.logger.info('Done.')

    def _try_to_copy_inputs(self):
        self.logger.info('Downloading input files')
        self._set_status(STATUS.COPYING_INPUTS)
        try:
            self._copy_inputs()
        except Exception as e:
            self._report_error(message='Failed to copy inputs to workspace', detail=str(e))
            raise e

    def _copy_inputs(self):
        if self.task_run_attempt.get('inputs') is None:
            self.logger.info('No inputs.')
            return
        file_data_object_ids = []
        for input in self.task_run_attempt['inputs']:
            if input['data_object']['type'] == 'file':
                file_data_object_ids.append('@'+input['data_object']['id'])
        self.logger.debug('Copying inputs %s to %s.' % ( file_data_object_ids, self.settings['WORKING_DIR']))
        self.filemanager.export_files(
            file_data_object_ids,
            destination_url=self.settings['WORKING_DIR'])

    def _try_to_create_run_script(self):
        self.logger.info('Creating run script')
        self._set_status(STATUS.CREATING_RUN_SCRIPT)
        try:
            self._create_run_script()
        except Exception as e:
            self._report_error(message-'Failed to create run script', detail=str(e))
            raise e

    def _create_run_script(self):
        user_command = self.task_run_attempt['task_definition']['command']
        with open(os.path.join(self.settings['WORKING_DIR'], self.LOOM_RUN_SCRIPT_NAME), 'w') as f:
            f.write(user_command + '\n')
        
    def _try_to_pull_image(self):
        self._set_status(STATUS.FETCHING_IMAGE)
        try:
            self._pull_image()
        except Exception as e:
            self._report_error(message='Failed to fetch image for runtime environment', detail=str(e))
            raise e

    def _pull_image(self):
        pull_data = self._parse_docker_output(self.docker_client.pull(self._get_docker_image()))
        if pull_data[-1].get('errorDetail'):
            raise ContainerPullError(pull_data[-1].get('errorDetail'))
        else:
            self.logger.debug(json.dumps(pull_data, indent=2, separators=(',', ': ')))

    def _get_docker_image(self):
        # Tag is required. Otherwise docker-py pull will download all tags.
        docker_image = self.task_run_attempt['task_definition']['environment']['docker_image']
        if not ':' in docker_image:
            docker_image = docker_image + ':latest'
        return docker_image
        
    def _parse_docker_output(self, data):
        return [json.loads(line) for line in data.strip().split('\r\n')]

    def _try_to_create_container(self):
        self._set_status(STATUS.CREATING_CONTAINER)
        try:
            self._create_container()
            self._set_container_id(self.container['Id'])
        except Exception as e:
            self._report_error(message='Failed to create container for runtime environment', detail=str(e))
            raise e

    def _create_container(self):
        docker_image = self._get_docker_image()
        interpreter = self.task_run_attempt['task_definition']['interpreter']
        host_dir = self.settings['WORKING_DIR']
        container_dir = '/loom_workspace'

        command = [
            interpreter,
            self.LOOM_RUN_SCRIPT_NAME
        ]

        self.container = self.docker_client.create_container(
            image=docker_image,
            command=command,
            volumes=[container_dir],
            host_config=self.docker_client.create_host_config(
                binds={host_dir: {
                    'bind': container_dir,
                    'mode': 'rw',
                }}),
            working_dir=container_dir,
        )

    def _try_to_run_container(self):
        self._set_status(STATUS.STARTING_ANALYSIS)
        try:
            self.docker_client.start(self.container)
            self._verify_container_started_running()
        except Exception as e:
            self._report_error(message='Failed to start analysis', detail=str(e))
            raise e

    def _verify_container_started_running(self):
        status = self.docker_client.inspect_container(self.container)['State'].get('Status')
        if status == 'running' or status == 'exited':
            return
        else:
            raise ContainerStartError('Unexpected container status "%s"' % status)

    def _try_to_get_returncode(self):
        self._set_status(STATUS.RUNNING_ANALYSIS)
        try:
            returncode = self._poll_for_returncode()
            if returncode == 0:
                return
            else:
                # bad returncode
                self._report_error(message='Analysis finished with a bad returncode %s' % returncode, detail='Returncode %s. Check stderr log for more information.' % returncode)
                # Do not raise error. Attempt to save log files.
        except Exception as e:
            self._report_error(message='An error prevented the analysis from finishing', detail=str(e))
            # Do not raise error. Attempt to save log files.

    def _poll_for_returncode(self, poll_interval_seconds=1, timeout_seconds=86400):
        start_time = datetime.now()

        while True:
            self._send_heartbeat()
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception('Process timed out after %s seconds' % time_running.seconds)

            try:
                container_data = self.docker_client.inspect_container(self.container)
            except Exception as e:
                raise Exception('Unable to inspect Docker container: "%s"' % str(e))

            if not container_data.get('State'):
                raise Exception('Could not parse container info from Docker: "%s"' % container_data)

            if container_data['State'].get('Status') == 'exited':
                # Success
                return container_data['State'].get('ExitCode')
            elif container_data['State'].get('Status') == 'running':
                time.sleep(poll_interval_seconds)
            else:
                # Error -- process did not complete
                message = 'Docker container has unexpected status "%s"' % \
                          container_data['State'].get('Status')
                raise Exception(message)

    def _try_to_save_process_logs(self):
        self.logger.debug('Saving process logs')
        try:
            self._save_process_logs()
        except Exception as e:
            self._report_error(message='Failed to save process logs', detail=str(e))
            # Don't raise error. Continue cleanup

    def _save_process_logs(self):
        try:
            self.container
        except AttributeError:
            self.logger.debug('No container, so no process logs to save.')
            return

        self._init_directory(os.path.dirname(self.settings['STDOUT_LOG_FILE']))
        with open(self.settings['STDOUT_LOG_FILE'], 'w') as stdoutlog:
            stdoutlog.write(
                self.docker_client.logs(self.container, stderr=False, stdout=True)
            )
        self._init_directory(os.path.dirname(self.settings['STDERR_LOG_FILE']))
        with open(self.settings['STDERR_LOG_FILE'], 'w') as stderrlog:
            stderrlog.write(
                self.docker_client.logs(self.container, stderr=True, stdout=False)
            )
        self._import_log_file(self.settings['STDOUT_LOG_FILE'])
        self._import_log_file(self.settings['STDERR_LOG_FILE'])

    def _import_log_file(self, filepath):
        try:
            self.filemanager.import_log_file(
                self.task_run_attempt,
                filepath,
            )
        except IOError:
            message = 'Failed to upload log file %s' % filename
            self.logger.error(message)
            raise FileImportError(message)

    def _try_to_save_outputs(self):
        try:
            self.container
        except AttributeError:
            self.logger.debug('No container, so no outputs to save.')
            return # Never ran. No outputs to save

        self.logger.debug('Saving outputs')
        try:
            self._save_outputs()
        except Exception as e:
            self._report_error(message='Failed to save outputs', detail=str(e))
            # Don't raise error. Continue cleanup

    def _save_outputs(self):
        for output in self.task_run_attempt['outputs']:
            if output['type'] == 'file':
                filename = output['source']['filename']
                try:
                    data_object = self.filemanager.import_result_file(
                        output,
                        os.path.join(self.settings['WORKING_DIR'], filename)
                    )
                    self.logger.debug('Saved file output "%s"' % data_object['id'])
                except IOError as e:
                    self._report_error(message='Failed to save output file %s' % filename, detail=str(e))
            else:
                if output['source'].get('filename'):
                    with open(
                            os.path.join(
                                self.settings['WORKING_DIR'],
                                output['source'].get('filename')),
                            'r') as f:
                        output_text = f.read()

                elif output['source'].get('stream'):
                    # Get result from stream
                    if output['source'].get('stream') == 'stdout':
                        output_text = self.docker_client.logs(self.container, stderr=False, stdout=True)
                    elif output['source'].get('stream') == 'stderr':
                        output_text = self.docker_client.logs(self.container, stderr=True, stdout=False)
                    else:
                        raise Exception('Could not save output "%s" because source is unknown stream type "%s"' %  (output['channel'], output['source']['stream']))
                else:
                    raise Exception('Could not save output "%s" because did not include a filename or a stream: "%s"' %  (output['channel'], output['source']))

                data_object = self._save_nonfile_output(output, output_text)
                self.logger.debug('Saved %s output "%s"' % (output['type'], data_object['id']))

    def _save_nonfile_output(self, output, output_text):
        data_type = output['type']
        data_object = {
            'type': data_type,
            data_type+'_content': {
                data_type+'_value': output_text
            }
        }
        output.update({'data_object': data_object})
        return self.connection.update_task_run_attempt_output(output['id'], output)

    def _try_to_save_monitor_log(self):
        self.logger.debug('Saving worker process monitor log')
        try:
            if not self.settings.get('LOG_FILE'):
                self.logger.debug('No log to save for process monitor, because we logged to stdout instead. Use "--log_file" if you want to save the output.')
                return True
            self._save_monitor_log()
        except Exception as e:
            self._report_error(message='Failed to save worker process monitor log', detail=str(e))
            # Don't raise error. Continue cleanup

    def _save_monitor_log(self):
        self._import_log_file(self.settings['LOG_FILE'])

    # Updates to TaskRunAttempt

    def _send_heartbeat(self):
        try:
            self.last_heartbeat
        except AttributeError:
            self.last_heartbeat = datetime.now()

        time_since_heartbeat = datetime.now() - self.last_heartbeat
        if time_since_heartbeat.seconds > self.HEARTBEAT_INTERVAL_SECONDS:
            self.connection.update_task_run_attempt(
                self.settings['TASK_RUN_ATTEMPT_ID'],
                {}
            )
            self.last_heartbeat = datetime.now()

    def _set_container_id(self, container_id):
        self.connection.update_task_run_attempt(
            self.settings['TASK_RUN_ATTEMPT_ID'],
            {'container_id': container_id}
        )

    def _set_status(self, status):
        self.logger.debug('Setting status to "%s"' % status)
        self.connection.update_task_run_attempt(
            self.settings['TASK_RUN_ATTEMPT_ID'],
            {'status': status}
        )

    def _report_error(self, message, detail):
        self.logger.error(message + ': ' + detail)
        self.connection.post_task_run_attempt_error(
            self.settings['TASK_RUN_ATTEMPT_ID'],
            {
                'message': message,
                'detail': detail
            })

    # Parser

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(self):
        parser = argparse.ArgumentParser(__file__)
        parser.add_argument('--run_attempt_id',
                            '-i',
                            required=True,
                            help='ID of TaskRunAttempt to be processed')
        parser.add_argument('--master_url',
                            '-u',
                            required=True,
                            help='URL of the Loom master server')
        parser.add_argument('--log_level',
                            '-l',
                            required=False,
                            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                            default='WARNING',
                            help='Log level')
        parser.add_argument('--log_file',
                            '-f',
                            required=False,
                            default=None,
                            help='Log file')
        return parser


# pip entrypoint requires a function with no arguments 
def main():

    run_error = None
    cleanup_error = None

    try:
        tr = TaskRunner()
        tr.run()
    except Exception as e:
        run_error = e

    try:
        tr.cleanup()
    except Exception as e:
        cleanup_error = e

    # Errors from initialization or run
    # take priority over errors from cleanup
    if run_error:
        raise run_error
    elif cleanup_error:
        raise cleanup_error

if __name__=='__main__':
    main()
