class Connection:

    def __init__(self, worker_settings, task_run_attempt):
        self.worker_settings = worker_settings
        self.task_run_attempt = task_run_attempt

    def get_worker_settings(self, id):
        return self.worker_settings

    def get_task_run_attempt(self, id):
        return self.task_run_attempt

    def update_task_run_attempt(self, id, data):
        self.task_run_attempt.update(data)

    def post_task_run_attempt_error(self, id, error):
        pass
        
        
class FileManager:

    def export_files(self, file_ids, destination_url):
        pass
    

class Args:
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
