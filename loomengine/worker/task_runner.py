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

    def __init__(self, args=None):
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
        self._init_logger()

        # Errors here can be logged but not reported to server
        try:
            self.connection = Connection(self.settings['MASTER_URL'])
        except Exception as e:
            self.logger.error('Failed to initialize server connection: "%s"' % str(e))
            raise e

        # Errors here can be both logged and reported to server
        try:
            self._init_task_run_attempt()
            self._set_monitor_status_to_initializing()
            self.filemanager = FileManager(self.settings['MASTER_URL'])
            self.settings.update(self._get_worker_settings())
            self._init_docker_client()
        except Exception as e:
            self._set_monitor_status_to_failed_to_initialize(e)
            raise e

    def _init_logger(self):
        self.logger = logging.getLogger(__name__)

        LEVELS = {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
        }
        log_level = LEVELS[self.settings['LOG_LEVEL']]
        self.logger.setLevel(log_level)
        if log_level != 'DEBUG':
            self.logger.raiseExceptions = False

        if self.settings['LOG_FILE'] is None:
            self._init_logger_stdout_handler()
        else:
            self._init_logger_file_handler()

    def _init_logger_stdout_handler(self):
        utils_logger = logging.getLogger(loomengine.utils.__name__)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        utils_logger.addHandler(logging.StreamHandler(sys.stdout))

    def _init_logger_file_handler(self):
        utils_logger = logging.getLogger(loomengine.utils.__name__)
        self._init_directory(os.path.dirname(self.settings['WORKER_LOG_FILE']))
        file_handler = logging.FileHandler(self.settings['WORKER_LOG_FILE'])
        file_handler.setFormatter(
            logging.Formatter('%(levelname)s [%(asctime)s] %(message)s'))
        self.logger.addHandler(file_handler)
        utils_logger.addHandler(file_handler)

        # Route stdout and stderr to logger
        stdout_logger = StreamToLogger(self.logger, logging.INFO)
        sys.stdout = stdout_logger
        stderr_logger = StreamToLogger(self.logger, logging.ERROR)
        sys.stderr = stderr_logger

    def _init_directory(self, directory):
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

    def run(self):
        try:
            self._try_to_copy_input_files()
            self._try_to_pull_image()
            self._try_to_create_container()
            self._try_to_run_container()
            self._try_to_get_returncode()
        except Exception as e:
            self.logger.error('Exiting with error: %s' % str(e))

        self.cleanup()
        self.logger.debug('Exiting.')

    def cleanup(self):
        self._set_monitor_status_to_saving_output_files()

        if self._try_to_save_process_logs() \
           and self._try_to_save_outputs() \
           and self._try_to_save_monitor_log():
            self._set_monitor_status_to_finished()
        else:
            self._set_monitor_status_to_failed_to_save_output_files()

    def _try_to_copy_input_files(self):
        self._set_monitor_status_to_copying_input_files()
        try:
            self._copy_input_files()
        except Exception as e:
            self._set_monitor_status_to_failed_to_copy_input_files(e)
            raise e

    def _copy_input_files(self):
        if self.task_run_attempt.get('inputs') is None:
            return
        file_data_object_ids = []
        for input in self.task_run_attempt['inputs']:
            if input['data_object']['type'] == 'file':
                file_data_object_ids.append('@'+input['data_object']['id'])
        self.filemanager.export_files(
            file_data_object_ids,
            destination_url=self.settings['WORKING_DIR'])

    def _try_to_pull_image(self):
        self._set_monitor_status_to_getting_runtime_environment_image()
        try:
            self._pull_image()
        except Exception as e:
            self._set_monitor_status_to_failed_to_get_runtime_environment_image(e)
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
        self._set_monitor_status_to_creating_runtime_environment()
        try:
            self._create_container()
            self._set_container_id(self.container['Id'])
        except Exception as e:
            self._set_monitor_status_to_failed_to_create_runtime_environment(e)
            raise e

    def  _create_container(self):
        docker_image = self._get_docker_image()
        user_command = self.task_run_attempt['task_definition']['command']
        host_dir = self.settings['WORKING_DIR']
        # container_dir = '/loom_workspace'

        command = [
            'bash',
            '-o', 'pipefail',
            '-c', user_command,
        ]

        self.container = self.docker_client.create_container(
            image=docker_image,
            command=command,
#            volumes=[container_dir],
#            host_config=self.docker_client.create_host_config(
#                binds={host_dir: {
#                    'bind': container_dir,
#                    'mode': 'rw',
#                }}),
#            working_dir=container_dir,
        )

    def _try_to_run_container(self):
        self._set_monitor_status_to_starting_run()
        try:
            import pdb; pdb.set_trace()
            self.docker_client.start(self.container)
            self._verify_container_started_running()
        except Exception as e:
            self._set_monitor_status_to_failed_to_start_run(str(e.message))
            raise e

    def _verify_container_started_running(self):
        status = self.docker_client.inspect_container(self.container)['State'].get('Status')
        if status == 'running' or status == 'exited':
            return
        else:
            raise ContainerStartError('Unexpected container status "%s"' % status)

    def _try_to_get_returncode(self):
        self._set_monitor_status_to_waiting_for_run()
        self._set_worker_process_status_to_running()
        try:
            returncode = self._poll_for_returncode()
            if returncode == 0:
                self._set_worker_process_status_to_finished_success()
            else:
                # bad returncode
                self._set_worker_process_status_to_finished_with_error(returncode)
        except Exception as e:
            self._set_worker_process_status_to_failed_without_completing()
            # Do not raise error. Attempt to save log files.

    def _poll_for_returncode(self, poll_interval_seconds=1, timeout_seconds=86400):
        start_time = datetime.now()

        while True:
            self._send_heartbeat()
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                message = 'Process timed out after %s seconds' % time_running.seconds
                raise Exception(message)

            try:
                container_data = self.docker_client.inspect_container(self.container)
            except Exception as e:
                raise Exception('Unable to inspect Docker container: "%s"' % str(e))

            if not container_data.get('State'):
                raise Exception('Could not parse container info from Docker: "%s"' % container_data)

            if container_data['State'].get('Status') == 'exited':
                # Success
                return container_data['State'].get('Pid')
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
            return True
        except Exception as e:
            self.logger.error('Failed to save process logs. %s' % str(e))
            return False

    def _save_process_logs(self):
        try:
            self.container
        except AttributeError:
            raise Exception('No process logs to save')

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
            raise Exception('No outputs to save')
            
        self.logger.debug('Saving outputs')
        try:
            self._save_outputs()
            return True
        except Exception as e:
            self.logger.error('Failed to save outputs. %s' % str(e))
            return False

    def _save_outputs(self):
        for output in self.task_run_attempt['outputs']:
            if output['type'] == 'file':
                filename = output['filename']
                try:
                    self.filemanager.import_result_file(
                        output,
                        os.path.join(self.settings['WORKING_DIR'], filename)
                    )
                except IOError:
                    self.logger.error('Failed to upload output file %s' % filename)
                    # TODO report failure due to missing file
                    # Catch error to continue uploading other files
            else:
                # TODO handle non-file output types
                raise Exception("Can't handle outputs of type %s" %
                                output['type'])

    def _try_to_save_monitor_log(self):
        self.logger.debug('Saving worker process monitor log')
        try:
            self._save_monitor_log()
            return True
        except Exception as e:
            self.logger.error('Failed to save worker process monitor log')
            return False

    def _save_monitor_log(self):
        self._import_log_file(self.settings['WORKER_LOG_FILE'])

    # Updates to WorkerProcessMonitor

    def _set_monitor_status(self, status, status_message=''):
        self.connection.update_worker_process_monitor(
            self.task_run_attempt['worker_process_monitor']['id'],
            {'status': status, 'status_message': status_message}
        )

    def _set_monitor_status_to_initializing(self):
        self.logger.debug('Initializing')
        self._set_monitor_status('initializing')

    def _set_monitor_status_to_failed_to_initialize(self, error):
        self.logger.error('Failed to initialize worker monitor\n' + str(error))
        self._set_monitor_status('failed_to_initialize')
            
    def _set_monitor_status_to_copying_input_files(self):
        self.logger.debug('Copying input files')
        self._set_monitor_status('copying_input_files')

    def _set_monitor_status_to_failed_to_copy_input_files(self, error):
        self.logger.error('Failed to copy input files to worker.\n' + str(error))
        self._set_monitor_status('failed_to_copy_input_files')

    def _set_monitor_status_to_getting_runtime_environment_image(self):
        self.logger.debug('Getting runtime environment image')
        self._set_monitor_status('getting_runtime_environment_image')

    def _set_monitor_status_to_failed_to_get_runtime_environment_image(self, error):
        self.logger.error('Failed to get runtime environment image.\n' + str(error))
        self._set_monitor_status('failed_to_get_runtime_environment_image')

    def _set_monitor_status_to_creating_runtime_environment(self):
        self.logger.debug('Creating runtime environment')
        self._set_monitor_status('creating_runtime_environment')

    def _set_monitor_status_to_failed_to_create_runtime_environment(self, error):
        self.logger.error('Failed to create runtime environment.\n' + str(error))
        self._set_monitor_status('creating_runtime_environment')

    def _set_monitor_status_to_starting_run(self):
        self.logger.debug('Attempting to run container')
        self._set_monitor_status('starting_run')

    def _set_monitor_status_to_failed_to_start_run(self, error):
        self.logger.error('Failed to start run.\n' + str(error))
        self._set_monitor_status('failed_to_start_run')

    def _set_monitor_status_to_waiting_for_run(self):
        self.logger.debug('Waiting for run')
        self._set_monitor_status('waiting_for_run')

    def _set_monitor_status_to_saving_output_files(self):
        self.logger.debug('Saving output files')
        self._set_monitor_status('saving_output_files')

    def _set_monitor_status_to_failed_to_save_output_files(self):
        self.logger.error('Failed to save output files')
        self._set_monitor_status('failed_to_save_output_files')

    def _set_monitor_status_to_finished(self):
        self.logger.debug('Monitor process is finished')
        self._set_monitor_status('finished')

    def _send_heartbeat(self):
        try:
            self.last_heartbeat
        except AttributeError:
            self.last_heartbeat = datetime.now()

        time_since_heartbeat = datetime.now() - self.last_heartbeat
        if time_since_heartbeat.seconds > self.HEARTBEAT_INTERVAL_SECONDS:
            self.connection.update_worker_process_monitor(
                self.task_run_attempt['worker_process_monitor']['id'],
                {}
            )
            self.last_heartbeat = datetime.now()

    # Updates to WorkerProcess

    def _set_worker_process_status(self, status, status_message=''):
        self.connection.update_worker_process(
            self.task_run_attempt['worker_process']['id'],
            {'status': status, 'status_message': status_message}
        )

    def _set_worker_process_status_to_running(self):
        self.logger.debug('Worker process is running')
        self._set_worker_process_status('running')

    def _set_worker_process_status_to_failed_without_completing(self, error):
        self.logger.error('Failed without finishing: "%s"' % str(error))
        self._set_worker_process_status('failed_without_completing')            

    def _set_worker_process_status_to_finished_with_error(self, returncode):
        message = 'Finished with error return code "%s". Check stderr log.' % returncode
        self.logger.error(message)
        self._set_worker_process_status(
            'finished_with_error',
            status_message=message)

    def _set_worker_process_status_to_failed_without_completing(self):
        self.logger.debug('Finished successfully')
        self._set_worker_process_status('finished_successfully')

    # Updates to TaskRunAttempt
    
    def _set_container_id(self, container_id):
        self.connection.update_worker_process(
            self.task_run_attempt['worker_process']['id'],
            {'container_id': container_id}
        )

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
    TaskRunner().run()

if __name__=='__main__':
    main()
