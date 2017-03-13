import copy
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Process any active Tasks'

    def handle(self, *args, **options):
        from api.tasks import process_active_tasks
        process_active_tasks()
