#!/usr/bin/env python
import requests

class DataNotFoundException(Exception):
    pass


class StepRunner:

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()

        self.RUN_ID = args.run_id
        self.MASTER_URL = args.master_url.rstrip('\\')
        self.FILE_SERVER = args.file_server
        self.FILE_ROOT = args.file_root

    def _get_step_run(self):
        url = self.MASTER_URL + '/api/step_runs/' + self.RUN_ID
        response = requests.get(url)
        if not response.status_code == 200:
            raise DataNotFoundException("Step run not found at url %s" % url)
        step_run = response.json()
        return step_run

    def _get_input_port_bundles(self, step_run_id):
        url = self.MASTER_URL + '/api/step_runs/' + self.RunID + '/input_port_bundles/'
        response = request.get(url)
        if not response.status_code == 200:
            raise DataNotFoundException("Input port bundles not found at url %s" % url)
        input_port_bundles = response.json()
        return input_port_bundles

    def run(self):
        step_run = self._get_step_run()

        # Get step_run
        # Initialize
        # Run
        # Cleanup

    def _get_args(self):
        parser = self._get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def _get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('step_runner')
        parser.add_argument('--run_id', '-i',
                            help="ID of step run to be executed")
        parser.add_argument('--master_url', '-m',
                            help="URL of master server")
        parser.add_argument('--file_server', '-f',
                            help="Hostname of file server. Used in recording results file locations.")
        parser.add_argument('--file_root', '-r',
                            help="Local path to root of working directories")
        return parser

if __name__=='__main__':
    # step_runner.py --run_id {RUN_ID} --server_url {URL} --file_server {FILE_SERVER} --file_root {FILE_ROOT}
    StepRunner().run()
