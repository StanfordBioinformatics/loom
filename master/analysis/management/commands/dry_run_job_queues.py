from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from analysis.models import Queues

class Command(BaseCommand):
    help = 'Checks and updates work in progress'

    @transaction.atomic
    def handle(self, *args, **options):
        Queues.update_and_dry_run()
