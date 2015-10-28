import logging

from django.conf import settings

from analysis.worker_manager.local import LocalWorkerManager
from analysis.worker_manager.cluster import ClusterWorkerManager

logger = logging.getLogger('XppfDaemon')

class WorkerManagerFactory:
    LOCAL = 'LOCAL'
    CLUSTER = 'ELASTICLUSTER'

    @classmethod
    def get_worker_manager(cls):
        logger.debug('Getting worker manager of type "%s"' % settings.WORKER_TYPE)
        if settings.WORKER_TYPE == cls.LOCAL:
            return LocalWorkerManager()
        elif settings.WORKER_TYPE == cls.CLUSTER:
            return ClusterWorkerManager()
        else:
            raise Exception('Invalid selection WORKER_TYPE=%s' % settings.WORKER_TYPE)
