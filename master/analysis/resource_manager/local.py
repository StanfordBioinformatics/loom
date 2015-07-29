import hashlib
import requests

from settings import BASEDIR

from analysis.models import StepResult


class LocalResourceManager:

    @classmethod
    def run(cls, step_run):
        # Create a background process to initialize, run, cleanup
        # Record in step_run.process_location
        
        pass

   """
        from analysis.models.queues import Queues
        # Generate a result,
        # post it to the web server.

        for output_port in step_run.step_definition.template.output_ports.all():

            result = {
                'step_definition': step_run.step_definition.to_obj(),
                'output_binding': {
                    'file': cls._render_dummy_file(),
                    'output_port': output_port.to_obj(),
                    },
                }

            # Post result
            Queues.submit_result({'step_run': step_run.to_json(), 'step_result': result})

        #Remove run from queue
        Queues.close_run(step_run.to_json())
"""
