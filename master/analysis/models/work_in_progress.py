from analysis.worker_manager.factory import WorkerManagerFactory
from django.db import models
import logging
from .run_requests import RunRequest, Workflow, Step
from .step_runs import StepRun, StepResult
from .common import AnalysisAppBaseModel


logger = logging.getLogger('xppf')

class WorkInProgress(AnalysisAppBaseModel):

    @classmethod
    def submit_new_request(cls, request_submission_obj_or_json):
        # This is called by a view when a new request is received
        request_submission = RunRequest.create(request_submission_obj_or_json)

    @classmethod
    def submit_result(cls, data_obj_or_json):
        data_obj = StepResult._any_to_obj(data_obj_or_json)
        step_run_obj = data_obj.get('step_run')
        step_run = StepRun.get_by_definition(step_run_obj)

        data_object = data_obj.get('step_result').get('data_object')
        step_definition_output_port = data_obj.get('step_result').get('output_port')

        return step_run.add_step_result(data_object, step_definition_output_port)
