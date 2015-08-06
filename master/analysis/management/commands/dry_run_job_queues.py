from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from analysis.models import WorkInProgress

class Command(BaseCommand):
    help = 'Checks and updates work in progress'

    @transaction.atomic
    def handle(self, *args, **options):
        WorkInProgress.update_and_dry_run()
