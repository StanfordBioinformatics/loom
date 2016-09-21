from loomengine.worker.test import fixtures

class Connection:

    worker_settings = {
        'STDOUT_LOG_FILE': '/tmp/stdout.log',
        'STDERR_LOG_FILE': '/tmp/stderr.log',
        'WORKING_DIR': '/tmp/work',
    }
    
    def __init__(self, worker_settings = None):
        if worker_settings:
            self.worker_settings = worker_settings

    def get_worker_settings(self, id):
        return self.worker_settings

    def get_task_run_attempt(self, id):        
        return fixtures.task_run_attempt

    def update_worker_process_monitor(self, id, data):
        self.monitor_status = data.get('status')

    def update_worker_process(self, id, data):
        self.process_status = data.get('status')

class FileManager:
    pass

class Args:
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
