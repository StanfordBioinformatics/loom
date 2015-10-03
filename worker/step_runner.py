#!/usr/bin/env python
from datetime import datetime
import json
import logging
import os
import errno
import requests
import string
import subprocess
import time

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from xppf.common import md5calc


class StepRunner:

    STEP_RUNS_DIR = 'step_runs'

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()

        self.RUN_ID = args.run_id
        self.MASTER_URL = args.master_url.rstrip('\\')

        self._init_worker_info()
        self._init_logger()

    def _init_worker_info(self):
        url = self.MASTER_URL + '/api/workerinfo'

        response = requests.get(url)
        response.raise_for_status()
        workerinfo = response.json()

        self.FILE_SERVER = workerinfo['workerinfo']['FILE_SERVER_FOR_WORKER']
        self.FILE_ROOT = workerinfo['workerinfo']['FILE_ROOT']
        self.LOGFILE = workerinfo['workerinfo']['WORKER_LOGFILE']
        self.LOG_LEVEL = workerinfo['workerinfo']['LOG_LEVEL']

    def _get_step_run(self):
        url = self.MASTER_URL + '/api/step_runs/' + self.RUN_ID
        response = requests.get(url)
        response.raise_for_status()
        step_run = response.json()
        self.logger.debug(step_run)
        return step_run

    def _get_input_port_bundles(self):
        url = self.MASTER_URL + '/api/step_runs/' + self.RUN_ID + '/input_port_bundles/'
        response = requests.get(url)
        response.raise_for_status()
        input_port_bundles = response.json()
        return input_port_bundles

    def _get_output_ports(self, step_run):
        output_ports = step_run.get('step_definition').get('template').get('output_ports')
        if output_ports is None:
            output_ports = []
        return output_ports

    def run(self):
        step_run = self._get_step_run()

        self._prepare_working_directory()
        inputs = self._get_input_port_bundles().get('input_port_bundles')
        output_ports = self._get_output_ports(step_run)
        self._prepare_all_inputs(inputs)
        process = self._execute(step_run)
        self._wait_for_process(process)
        (results, locations) = self._process_outputs(output_ports, step_run.get('step_definition'))
        self._save_results(results, locations, step_run)
        self._flag_run_as_complete(step_run)

    def _prepare_working_directory(self):
        self.WORKING_DIR = os.path.join(
            self.FILE_ROOT, 
            self.STEP_RUNS_DIR,
            "%s_%s" % (
                datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss"),
                self.RUN_ID[0:10],
                ))
        try:
            os.makedirs(self.WORKING_DIR)
            self.logger.debug('Created %s' % self.WORKING_DIR)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(self.WORKING_DIR):
                self.logger.debug('Directory %s exists, no need to create' % self.WORKING_DIR) 
            else:
                raise

    def _prepare_all_inputs(self, input_port_bundles):
        if input_port_bundles is None:
            return
        for bundle in input_port_bundles:
            self._prepare_port_inputs(bundle)

    def _prepare_port_inputs(self, input_port_bundle):
        port = input_port_bundle['input_port']
        files_and_locations = input_port_bundle.get('files_and_storage_locations')
        if files_and_locations is None:
            return
        for f in files_and_locations:
            self._prepare_input(f, port)

    def _prepare_input(self, file_and_locations, port):
        cmd = ['ln',
               self._select_location(file_and_locations.get('file_storage_locations')),
               self._get_file_path(port)]
        subprocess.call(cmd)

    def _select_location(self, locations):
        return locations[0]['file_path']

    def _execute(self, step_run):
        step_definition = step_run.get('step_definition')
        template = step_definition.get('template')
        environment = template.get('environment')
        docker_image = environment.get('docker_image')
        raw_command = template.get('command')
        command = self._process_command(raw_command, step_run)
        host_dir = self.WORKING_DIR
        container_dir = '/working_dir'
        command_template = string.Template('docker run --rm -v ${host_dir}:${container_dir}:rw -w ${container_dir} $docker_image sh -c \'$command\'') #TODO - need sudo?
        full_command = command_template.substitute(container_dir=container_dir, host_dir=host_dir, docker_image=docker_image, command=command)
        self.logger.debug(full_command)
        return subprocess.Popen(full_command, shell=True)

    def _process_command(self, raw_command, step_run):
#        template_dict = TemplateDict(step_run)
        return raw_command

    def _wait_for_process(self, process, poll_interval_seconds=1, timeout_seconds=86400):
        start_time = datetime.now()
        while True:
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")
            returncode = process.poll()
            if returncode is not None:
                break
            time.sleep(poll_interval_seconds)
        if returncode == 0:
            return
        else:
            raise Exception('Process returned with error %s' % str(returncode))

    def _process_outputs(self, output_ports, step_definition):
        results = []
        locations = []
        for output_port in output_ports:
            results.append(self._get_result_obj(output_port, step_definition))
            locations.append(self._get_location_obj(output_port))
        return (results, locations)

    def _get_file_path(self, port):
        return os.path.join(
            self.WORKING_DIR,
            port.get('file_path')
            )


    def _get_location_obj(self, output_port):
        location = {
            'file_contents': self._get_file_obj(self._get_file_path(output_port))['file_contents'],
            'file_path': self._get_file_path(output_port),
            'host_url': self.FILE_SERVER,
            }
        return location

    def _get_result_obj(self, output_port, step_definition):
        result = {
            'step_definition': step_definition,
            'output_binding': {
                'data_object': self._get_file_obj(self._get_file_path(output_port)),
                'output_port': output_port,
                },
            }
        return result

    def _get_file_obj(self, file_path):
        file = {
            'file_contents': {
                'hash_value': md5calc.calculate_md5sum(file_path),
                'hash_function': 'md5',
                }
            }
        return file

    def _save_results(self, results, locations, step_run):
        for result in results:
            self._save_result(result, step_run)
        for location in locations:
            self._save_location(location)

    def _save_location(self, location):
        response = requests.post(self.MASTER_URL+'/api/file_storage_locations', data=json.dumps(location))
        response.raise_for_status()

    def _save_result(self, result, step_run):
        data = {
            'step_run': step_run,
            'step_result': result,
            }
        response = requests.post(self.MASTER_URL+'/api/submitresult', data=json.dumps(data))
        response.raise_for_status()

    def _flag_run_as_complete(self, step_run):
        update_data = {'is_complete': True}
        url = self.MASTER_URL+'/api/step_runs/%s' % step_run.get('_id')
        self.logger.debug('updating StepRun at url '+url)
        response = requests.post(url, data=json.dumps(update_data))
        response.raise_for_status()

    def _get_args(self):
        parser = self._get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def _get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('step_runner')
        parser.add_argument('--run_id', '-i',
                            help="ID of step run to be executed",
                            required=True)
        parser.add_argument('--master_url', '-m',
                            help="URL of master server",
                            required=True)
        return parser

    def _init_logger(self):
        self.logger = logging.getLogger("XppfWorker")
        self.logger.setLevel(self.LOG_LEVEL)
        formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
        handler = self._init_handler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _init_handler(self):
        if self.LOGFILE is None:
            return logging.StreamHandler()
        else:
            return logging.FileHandler(self.LOGFILE)


if __name__=='__main__':
    StepRunner().run()
