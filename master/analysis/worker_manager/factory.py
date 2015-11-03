import logging
from django.conf import settings
from .dummy import DummyWorkerManager
from .local import LocalWorkerManager
from .cluster import ClusterWorkerManager

logger = logging.getLogger('LoomDaemon')

class WorkerManagerFactory:
    LOCAL = 'LOCAL'
    DUMMY = 'DUMMY'
    CLUSTER = 'ELASTICLUSTER'

    @classmethod
    def get_worker_manager(cls):
        logger.debug('Getting worker manager of type "%s"' % settings.WORKER_TYPE)
        if settings.WORKER_TYPE == cls.LOCAL:
            return LocalWorkerManager()
        if settings.WORKER_TYPE == cls.CLUSTER:
            return ClusterWorkerManager()
        elif settings.WORKER_TYPE == cls.DUMMY:
            return DummyWorkerManager()
        else:
            raise Exception('Invalid selection WORKER_TYPE=%s' % settings.WORKER_TYPE)
