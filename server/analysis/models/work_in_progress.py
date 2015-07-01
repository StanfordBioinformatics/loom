from django.db import models

from .requests import Request
from .runs import AnalysisRun, StepRun
from .common import AnalysisAppBaseModel


class WorkInProgress(AnalysisAppBaseModel):
    open_requests = models.ManyToManyField('Request')
    running_analyses = models.ManyToManyField('AnalysisRun')
    running_steps = models.ManyToManyField('StepRun')
    ready_analyses = models.ManyToManyField('AnalysisRequest')
    ready_steps = models.ManyToManyField('StepRequest')

    @classmethod
    def update(cls):
        # This method is periodically called asynchronously

        wip = cls._get_wip_singleton()

        wip._run_ready_analyses()
        wip._update_ready_steps()
        wip._run_ready_steps()

    @classmethod
    def _get_wip_singleton(cls):
        objects = cls.objects.all()
        if len(objects) > 1:
            raise Exception('Error: More than 1 WorkInProgress objects exist. This should be a singleton.')
        elif len(objects) < 1:
            wip = WorkInProgress()
            wip.save()
            return wip
        else:
            return objects[0]

    @classmethod
    def submit_new_request(cls, request_obj_or_json):
        # This is called by a view when a new request is received
        wip = cls._get_wip_singleton()
        request = Request.create(request_obj_or_json)
        wip._add_open_request(request)

    def _add_open_request(self, request):
        self.open_requests.add(request)
        for analysis in request.get_analyses():
            self._add_ready_analysis(analysis)

    def _add_ready_analysis(self, analysis):
        self.ready_analyses.add(analysis)

    def _remove_ready_analysis(self, analysis):
        self.ready_analyses.remove(analysis)

    def _add_running_analysis(self, analysis):
        self.running_analyses.add(analysis)

    def _add_ready_step(self, step):
        self.ready_steps.add(step)

    def _add_running_step(self, step_run):
        self.running_steps.add(step_run)

    def _run_ready_analyses(self):
        for analysis in self.ready_analyses.all():
            steps_runs = []
            for step_request in analysis.steps.all():
                step_run = {
                    'step': step_request.render_step()
                    }
                steps_runs.append(step_run)

            analysis_run = AnalysisRun.create(
                {
                    'analysis_request': analysis.to_obj(),
                    'step_runs': step_runs,
                    }
                )
            self._add_running_analysis(analysis_run)
            self._remove_ready_analysis(analysis)

    def _update_ready_steps(self):
        for analysis in self.running_analyses.all():
            for step in analysis.get_ready_steps():
                self._add_ready_step(step)

    def _run_step(self, step):
        step_run = StepRun({'step': step})
        self._add_running_step(self, step_run)
