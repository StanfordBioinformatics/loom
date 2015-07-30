import logging
from django.conf import settings
from .dummy import DummyResourceManager
from .local import LocalResourceManager

logger = logging.getLogger('xppf')

class ResourceManagerFactory:
    LOCAL = 'LOCAL'
    DUMMY = 'DUMMY'

    @classmethod
    def get_resource_manager(cls):
        logger.debug('Getting resource manager of type "%s"' % settings.RESOURCE_MANAGER)
        if settings.RESOURCE_MANAGER == cls.LOCAL:
            return LocalResourceManager()
        elif settings.RESOURCE_MANAGER == cls.DUMMY:
            return DummyResourceManager()
        else:
            raise Exception('Invalid selection RESOURCE_MANAGER=%s' % settings.RESOURCE_MANAGER)
