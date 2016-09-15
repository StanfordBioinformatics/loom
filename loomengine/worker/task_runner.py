#!/usr/bin/env python

import argparse
import copy
from datetime import datetime
import errno
import logging
import os
import docker
import requests
import string
import subprocess
import sys
import time
import uuid

from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection
from loomengine.utils.logger import StreamToLogger

class TaskRunner(object):

    DOCKER_SOCKET = 'unix://var/run/docker.sock'

    def __init__(self, args=None):
        if args is None:
            args = self._get_args()
        self.settings = {
            'TASK_RUN_ATTEMPT_ID': args.run_attempt_id,
            'MASTER_URL': args.master_url
        }
        self._init_docker_client()
        self._init_connection()
        self.settings.update(self._get_worker_settings())
        self._init_directories()
        self._init_logger()
        self._init_filemanager()
        self._init_task_run_attempt()

    def _init_docker_client(self):
        self.docker_client = docker.Client(base_url=self.DOCKER_SOCKET)

    def _init_connection(self):
        self.connection = Connection(self.settings['MASTER_URL'])

    def _init_filemanager(self):
        self.filemanager = FileManager(self.settings['MASTER_URL'], logger=self.logger)

    def _get_worker_settings(self):
        return self.connection.get_worker_settings(self.settings['TASK_RUN_ATTEMPT_ID'])

    def _init_directories(self):
        for directory in set([self.settings['WORKING_DIR'],
                              os.path.dirname(self.settings['WORKER_LOG_FILE']),
                              os.path.dirname(self.settings['STDOUT_LOG_FILE']),
                              os.path.dirname(self.settings['STDERR_LOG_FILE']),
        ]):
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
            except OSError as e:
                raise Exception('Failed to create directory %s. %s' % (directory, e.strerror))

    def _init_logger(self):
        self.logger = logging.getLogger("LoomWorker")
        self.logger.setLevel(self.settings['LOG_LEVEL'])
        self.logger.raiseExceptions = True
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
        handler = self._init_handler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        stdout_logger = StreamToLogger(self.logger, logging.INFO)
        sys.stdout = stdout_logger
        stderr_logger = StreamToLogger(self.logger, logging.ERROR)
        sys.stderr = stderr_logger
    
    def _init_handler(self):
        if self.settings.get('WORKER_LOG_FILE') is None:
            return logging.StreamHandler()
        else:
            if not os.path.exists(os.path.dirname(self.settings['WORKER_LOG_FILE'])):
                os.makedirs(os.path.dirname(self.settings['WORKER_LOG_FILE']))
            return logging.FileHandler(self.settings['WORKER_LOG_FILE'])

    def _init_task_run_attempt(self):
        self.task_run_attempt = self.connection.get_task_run_attempt(self.settings['TASK_RUN_ATTEMPT_ID'])
        if self.task_run_attempt is None:
            raise Exception('TaskRunAttempt ID "%s" not found' % self.settings['TASK_RUN_ATTEMPT_ID'])

    def run(self):
        self._export_inputs()

        self._set_process_status('preparing_runtime_environment')

        with open(self.settings['STDOUT_LOG_FILE'], 'w') as stdoutlog:
            with open(self.settings['STDERR_LOG_FILE'], 'w') as stderrlog:
                self._prepare_container(stdoutlog, stderrlog)
                self._run_container(stdoutlog, stderrlog)

        self._set_process_status('running')

        returncode = self._poll_for_returncode()

        if returncode == 0:
            self._set_process_status('finished_success')
        else:
            err_message = 'Worker process failed with nonzero returncode %s. \nFor more '\
                          'information check the stderr log file' % str(process.returncode)
            self.logger.error(err_message)
            self._set_process_status('finished_with_error')

        self._import_outputs()
        self._import_log_files()

        self._set_task_run_attempt_status('complete')

    def _set_task_run_attempt_status(self, status):
        task_run_attempt = copy.deepcopy(self.task_run_attempt)
        task_run_attempt.update({'status': status})
        
        self.connection.update_task_run_attempt(
            task_run_attempt['id'],
            task_run_attempt)

    def _export_inputs(self):
        if self.task_run_attempt.get('inputs') is None:
            return
        file_data_object_ids = []
        for input in self.task_run_attempt['inputs']:
            if input['data_object']['type'] == 'file':
                file_data_object_ids.append('@'+input['data_object']['id'])
        self.filemanager.export_files(
            file_data_object_ids,
            destination_url=self.settings['WORKING_DIR'])

    def _import_outputs(self):
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

    def _import_log_files(self):
        for log_file in (self.settings['WORKER_LOG_FILE'],
                        self.settings['STDOUT_LOG_FILE'],
                        self.settings['STDERR_LOG_FILE']):
            try:
                self.filemanager.import_log_file(
                    self.task_run_attempt,
                    log_file
                )
            except IOError:
                self.logger.error('Failed to upload log file %s' % filename)

    def _prepare_container(self, stdoutlog, stderrlog):
        self._pull_image_if_not_local()
        self._create_container()
        self._set_container_id(self.container['Id'])

    def _run_container(self, stdoutlog, stderrlog):
        self.docker_client.start(self.container)
        self._verify_container_started_running()

    def _pull_image_if_not_local(self):
        docker_image = self.task_run_attempt['task_definition']['environment']['docker_image']
        try:
            self.docker_client.inspect_image(docker_image)
        except docker.errors.NotFound:
            # Image is not available locally. Pull it now.
            pull_data = self.docker_client.pull(docker_image)
            if pull_data.get('errorDetail'):
                import pdb; pdb.set_trace()
                # Error
                pass

    def  _create_container(self):
        docker_image = self.task_run_attempt['task_definition']['environment']['docker_image']
        user_command = self.task_run_attempt['task_definition']['command']
        host_dir = self.settings['WORKING_DIR']
        container_dir = '/loom_workspace'

        command = [
            'bash',
            '-o',
            'pipefail',
            '-c',
            user_command,
        ]

        # may raise docker.errors.NotFound
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

    def _verify_container_started_running(self):
        status = self.docker_client.inspect_container(self.container)['State'].get('Status')
        if status == 'running' or status == 'exited':
            return
        else:
            #TODO
            raise Exception()

    def _poll_for_returncode(self, poll_interval_seconds=1, timeout_seconds=86400):
        start_time = datetime.now()
        while True:
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")

            container_data = self.docker_client.inspect_container(self.container)

            if container_data['State'].get('Status') == 'exited':
                return container_data['State'].get('Pid')
            elif container_data['State'].get('Status') == 'running':
                time.sleep(poll_interval_seconds)
            else:
                raise Exception() # TODO

    def _set_process_status(self, status):
        self.connection.update_worker_process(
            self.task_run_attempt['worker_process']['id'],
            {'status': status}
        )

    def _set_container_id(self, container_id):
        self.connection.update_worker_process(
            self.task_run_attempt['worker_process']['id'],
            {'container_id': container_id}
        )

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
        return parser


# pip entrypoint requires a function with no arguments 
def main():
    TaskRunner().run()

if __name__=='__main__':
    main()
