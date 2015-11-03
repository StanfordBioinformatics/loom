from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from analysis.models import RunRequest
from xppfdaemon import xppf_daemon_logger

logger = xppf_daemon_logger.get_logger()

class Command(BaseCommand):
    help = 'Checks and updates work in progress'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            RunRequest.update_and_dry_run()
        except Exception as e:
            logger.exception(e)
            raise
