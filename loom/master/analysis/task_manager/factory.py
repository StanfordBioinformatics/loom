import abc
import logging

from django.conf import settings

from analysis import get_setting
from analysis.task_manager.local import LocalTaskManager
from analysis.task_manager.cluster import ClusterTaskManager
from analysis.task_manager.cloud import CloudTaskManager
from analysis.task_manager.mock import MockTaskManager

logger = logging.getLogger('LoomDaemon')

class TaskManagerFactory:
    
    # Worker types
    LOCAL = 'LOCAL'
    CLUSTER = 'ELASTICLUSTER'
    GOOGLE_CLOUD = 'GOOGLE_CLOUD'
    MOCK = 'MOCK'

    @classmethod
    def get_task_manager(cls, is_mock=False):
        if is_mock == True:
            return MockTaskManager()
        
        logger.debug('Getting task manager of type "%s"' % get_setting('WORKER_TYPE'))
        if get_setting('WORKER_TYPE') == cls.LOCAL:
            return LocalTaskManager()
        elif get_setting('WORKER_TYPE') == cls.CLUSTER:
            return ClusterTaskManager()
        elif get_setting('WORKER_TYPE') == cls.GOOGLE_CLOUD:
            return CloudTaskManager()
        elif get_setting('WORKER_TYPE') == cls.MOCK:
            return MockTaskManager()
        else:
            raise Exception('Invalid selection WORKER_TYPE=%s' % get_setting('WORKER_TYPE'))


class TaskManager:
    __metaclass__ = abc.ABCMeta
    """ Abstract base class for TaskManagers."""
    
    @abc.abstractmethod
    def run(cls, task_run):
        """ Subclasses are required to implement this function prototype."""
        pass

TaskManager.register(LocalTaskManager)
TaskManager.register(ClusterTaskManager)
TaskManager.register(CloudTaskManager)
TaskManager.register(MockTaskManager)
