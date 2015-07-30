from django.db import models
import logging

from .requests import Request, AnalysisRequest, StepRequest
from .runs import StepRun
from .results import StepResult
from .common import AnalysisAppBaseModel
from analysis.resource_manager.factory import ResourceManagerFactory

logger = logging.getLogger('xppf')
resource_manager = ResourceManagerFactory.get_resource_manager()

class Queues(AnalysisAppBaseModel):
    _class_name = ('queues', 'queues')

    open_requests = models.ManyToManyField('Request')
    open_analyses = models.ManyToManyField('AnalysisRequest')
    steps_ready_to_run = models.ManyToManyField('StepRun', related_name='ready_to_run_queue')
    steps_running = models.ManyToManyField('StepRun', related_name='running_queue')

    @classmethod
    def update_and_run(cls):
        logger.debug('Updating queues')
        # This method is periodically called asynchronously
        q = cls._get_queue_singleton()
        q._update_steps_ready_to_run()
        q._run_ready_steps()

    @classmethod
    def update_and_dry_run(cls):
        # For testing only
        q = cls._get_queue_singleton()
        q._update_steps_ready_to_run()

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

    @classmethod
    def submit_result(cls, data_obj_or_json):
        data_obj = StepResult._any_to_obj(data_obj_or_json)
        step_run_obj = data_obj.get('step_run')
        step_run = StepRun.get_by_definition(step_run_obj)
        step_result_obj = data_obj.get('step_result')
        step_result = step_run.add_step_result(step_result_obj)
        return step_result

    @classmethod
    def close_run(cls, step_run_obj_or_json):
        step_run = StepRun.get_by_definition(step_run_obj_or_json)
        q = cls._get_queue_singleton()
        q._remove_step_running(step_run)
        step_run.update({'is_complete': True})

    def _update_steps_ready_to_run(self):
        logger.debug('Updating steps ready to run...')
        for analysis in self.open_analyses.all():
            logger.debug('...checking analysis %s' % analysis._id)
            for step in analysis.get_steps_ready_to_run():
                logger.debug('...ready to run step %s' % step._id)
                step.attach_to_run_if_one_exists()
                if not step.has_run():
                    step.create_step_run()
                    self._add_step_ready_to_run(step.step_run)
                    logger.debug('...created a new StepRun with id %s' % step.step_run._id)
                else:
                    logger.debug('...found a matching StepRun with id %s' % step.step_run._id)

    def _run_ready_steps(self):
        logger.debug('Running ready steps...')
        for step in self.steps_ready_to_run.all():
            logger.debug('...transfering to steps_running queue and sending to resource manager, StepRun %s' % step._id)
            self._add_step_running(step)
            self._remove_step_ready_to_run(step)
            resource_manager.run(step)

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

    def _remove_step_running(self, step_run):
        self.steps_running.remove(step_run)

    @classmethod
    def print_queue(cls):
        q = cls._get_queue_singleton()
        print "Open requests (%s):" % q.open_requests.count()
        for request in q.open_requests.all():
            print request
        print "Open analyses (%s):" % q.open_analyses.count()
        for analysis in q.open_analyses.all():
            print analysis
        print "Steps ready to run (%s):" % q.steps_ready_to_run.count()
        for step_run in q.steps_ready_to_run.all():
            print step_run
        print "Steps running (%s):" % q.steps_running.count()
        for step_run in q.steps_running.all():
            print step_run
