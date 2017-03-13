import copy
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Create ready tasks from any active StepRuns'

    def handle(self, *args, **options):
        from api.tasks import process_active_step_runs
        process_active_step_runs()
