import abc
import logging

from django.conf import settings

from api import get_setting
from api.task_manager.local import LocalTaskManager
from api.task_manager.cloud import CloudTaskManager
from api.task_manager.mock import MockTaskManager

logger = logging.getLogger(__name__)

class TaskManagerFactory:
    
    # Worker types
    LOCAL = 'LOCAL'
    GOOGLE_CLOUD = 'GOOGLE_CLOUD'
    MOCK = 'MOCK'

    @classmethod
    def get_task_manager(cls):
        logger.debug('Getting task manager of type "%s"'
                     % get_setting('WORKER_TYPE'))
        if get_setting('WORKER_TYPE') == cls.LOCAL:
            return LocalTaskManager()
        elif get_setting('WORKER_TYPE') == cls.GOOGLE_CLOUD:
            return CloudTaskManager()
        elif get_setting('WORKER_TYPE') == cls.MOCK:
            return MockTaskManager()
        else:
            raise Exception('Invalid selection WORKER_TYPE=%s' %
                            get_setting('WORKER_TYPE'))


class TaskManager:
    __metaclass__ = abc.ABCMeta
    """ Abstract base class for TaskManagers."""
    
    @abc.abstractmethod
    def run(cls, task_run):
        """ Subclasses are required to implement this function prototype."""
        pass

TaskManager.register(LocalTaskManager)
TaskManager.register(CloudTaskManager)
TaskManager.register(MockTaskManager)
