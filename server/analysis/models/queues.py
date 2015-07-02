from django.db import models

from .requests import Request, AnalysisRequest, StepRequest
from .runs import StepRun
from .common import AnalysisAppBaseModel
from analysis.resource_manager import ResourceManager

class Queues(AnalysisAppBaseModel):
    open_requests = models.ManyToManyField('Request')
    open_analyses = models.ManyToManyField('AnalysisRequest')
    steps_ready_to_run = models.ManyToManyField('StepRun', related_name='ready_to_run_queue')
    steps_running = models.ManyToManyField('StepRun', related_name='running_queue')

    @classmethod
    def update_and_run(cls):
        # This method is periodically called asynchronously

        q = cls._get_queue_singleton()
        q._update_steps_ready_to_run()
        q._run_ready_steps()

    @classmethod
    def _get_queue_singleton(cls):
        q_objects = cls.objects.all()
        if q_objects.count() > 1:
            raise Exception('Error: More than 1 WorkInProgress objects exist. This should be a singleton.')
        elif q_objects.count() < 1:
            q = Queues()
            q.save()
            return q
        else:
            return q_objects.first()

    @classmethod
    def submit_new_request(cls, request_obj_or_json):
        # This is called by a view when a new request is received
        request = Request.create(request_obj_or_json)
        q = cls._get_queue_singleton()
        q._add_open_request(request)

    def _update_steps_ready_to_run(self):
        for analysis in self.open_analyses.all():
            for step in analysis.get_steps_ready_to_run():
                step.attach_to_run_if_one_exists()
                if not step.has_run():
                    step.create_step_run()
                    self._add_step_ready_to_run(step.step_run)

    def _run_ready_steps(self):
        for step in self.steps_ready_to_run.all():
            
            ResourceManager.run(step)
            self._add_step_running(step)
            self._remove_step_ready_to_run(step)

    def _add_open_request(self, request):
        self.open_requests.add(request)
        for analysis in request.get_analyses():
            self._add_open_analysis(analysis)

    def _add_open_analysis(self, analysis):
        self.open_analyses.add(analysis)

    def _remove_open_analysis(self, analysis):
        self.open_analyses.remove(analysis)

    def _add_step_ready_to_run(self, step):
        self.steps_ready_to_run.add(step)

    def _remove_step_ready_to_run(self, step):
        self.steps_ready_to_run.remove(step)

    def _add_step_running(self, step_run):
        self.steps_running.add(step_run)

