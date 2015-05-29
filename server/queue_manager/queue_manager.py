from analyses.models import *

class QueueManager(models.Manager):
    def get_ready_session_recipe(self):
        """ Return one SessionRecipe that is ready to run, and not already running."""
        pass

    def get_ready_session_recipes(self):
        """ Return all SessionRecipes that are ready to run."""
        ready_pks = []
        for session_recipe in SessionRecipes.objects.all():
            if session_recipe.is_ready():
                ready_pks.append(session_recipe.pk) 
        return SessionRecipe.objects.filter(pk__in=ready_pks)

    def get_running_session_recipes(self):
        """ Return all currently running SessionRecipes."""
        session_runs = SessionRun.objects.all()
        return SessionRecipe.objects.filter(sessionrun__in=session_runs)

    def get_session_recipes_to_run(self):
        """ Return all SessionRecipes that are ready to run, and not already running."""
        return self.get_ready_session_recipes().exclude(self.get_running_session_recipes())
