from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from analysis.models import Workflow
from loomdaemon import loom_daemon_logger

logger = loom_daemon_logger.get_logger()

class Command(BaseCommand):
    help = 'Checks and updates work in progress'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            Workflow.update_and_dry_run()
        except Exception as e:
            logger.exception(e)
            raise
