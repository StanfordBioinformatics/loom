from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from loomdaemon import loom_daemon_logger


class Command(BaseCommand):
    help = 'Refresh status for all runs'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument('--logfile',
            dest='logfile',
            default=None,
            help='Log file path')

    def handle(self, *args, **options):
        logfile = options.get('logfile')
        logger = loom_daemon_logger.get_logger(logfile)
        try:
            response = requests.post(settings.MASTER_URL_FOR_SERVER+'/api/controls/refresh/', verify=False)
            logger.debug(response.text)
        except Exception as e:
            logger.exception(e)
            raise
