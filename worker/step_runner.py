#!/usr/bin/env python
from datetime import datetime
import json
import logging
import os
import requests
import string
import subprocess
import time

from xppf.utils import md5calc

class DataNotFoundException(Exception):
    pass

class StepRunner:

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

        self.FILE_SERVER = workerinfo['workerinfo']['FILE_SERVER']
        self.FILE_ROOT = workerinfo['workerinfo']['FILE_ROOT']
        self.LOGFILE = workerinfo['workerinfo']['WORKER_LOGFILE']
        self.LOG_LEVEL = workerinfo['workerinfo']['LOG_LEVEL']

    def _get_step_run(self):
        url = self.MASTER_URL + '/api/step_runs/' + self.RUN_ID
        response = requests.get(url)
        if not response.status_code == 200:
            raise DataNotFoundException("Step run not found at url %s" % url)
        step_run = response.json()
        self.logger.debug(step_run)
        return step_run

    def _get_input_port_bundles(self):
        url = self.MASTER_URL + '/api/step_runs/' + self.RUN_ID + '/input_port_bundles/'
        response = requests.get(url)
        if not response.status_code == 200:
            raise DataNotFoundException("Input port bundles not found at url %s" % url)
        input_port_bundles = response.json()
        return input_port_bundles

    def _get_output_ports(self, step_run):
        output_ports = step_run.get('step_definition').get('template').get('output_ports')
        if output_ports is None:
            output_ports = []
        return output_ports

    def run(self):
        step_run = self._get_step_run()
        inputs = self._get_input_port_bundles().get('input_port_bundles')
        output_ports = self._get_output_ports(step_run)

        self._prepare_inputs(inputs)
        process = self._execute(step_run)
        self._wait_for_process(process)

        results = self._process_outputs(output_ports, step_run.get('step_definition'))
        self._save_results(results, step_run)

    def _prepare_inputs(self, inputs):
        if inputs is None:
            return
        for input in inputs:
            self._prepare_input(input)

    def _prepare_input(self, input):
        #TODO
        pass

    def _execute(self, step_run):
        step_definition = step_run.get('step_definition')
        template = step_definition.get('template')
        environment = template.get('environment')
        docker_image = environment.get('docker_image')
        command = template.get('command')
        host_dir = self.FILE_ROOT
        container_dir = '/working_dir'
        cmd_template = string.Template('docker run --rm -v ${host_dir}:${container_dir}:rw -w ${container_dir} $docker_image sh -c \'$command\'') #TODO - need sudo?
        cmd = cmd_template.substitute(container_dir=container_dir, host_dir=host_dir, docker_image=docker_image, command=command)
        self.logger.debug(cmd)
        return subprocess.Popen(cmd, shell=True)

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
        for output_port in output_ports:
            results.append(self._process_output(output_port, step_definition))
        return results

    def _process_output(self, output_port, step_definition):
        result = {
            'step_definition': step_definition,
            'output_binding': {
                'file': self._get_file_obj(
                    os.path.join(
                        self.FILE_ROOT,
                        output_port.get('file_path')
                        )
                    ),
                'output_port': output_port,
                },
            }
        return result

    def _get_file_obj(self, file_path):
        file = {
            'hash_value': md5calc.calculate_md5sum(file_path),
            'hash_function': 'md5',
            }
        return file

    def _save_results(self, results, step_run):
        for result in results:
            self._save_result(result, step_run)

    def _save_result(self, result, step_run):
        data = {
            'step_run': step_run,
            'step_result': result,
            }
        requests.post(self.MASTER_URL+'/api/submitresult', data=json.dumps(data))
        # TODO verify

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
