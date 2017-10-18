import copy
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Placeholder for debug code'

    def handle(self, *args, **options):
        self.stdout.write("Running debug command...")

        # DEBUG code goes here
