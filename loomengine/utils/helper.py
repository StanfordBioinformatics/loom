import os

def wait_for_true(test_method, timeout_seconds=20, sleep_interval=None):
    from datetime import datetime
    import time

    if sleep_interval is None:
        sleep_interval = timeout_seconds/10.0
    start_time = datetime.now()
    while not test_method():
        time.sleep(sleep_interval)
        time_running = datetime.now() - start_time
        if time_running.seconds > timeout_seconds:
            raise Exception("Timeout")

def init_directory(directory, new=False):
    if new and os.path.exists(directory):
        raise Exception('Directory %s already exists' % directory)
    if os.path.exists(directory) and not os.path.isdir(directory):
        raise Exception('Cannot initialize directory %s since a file exists with that name' % directory)
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError as e:
        raise Exception('Failed to create directory %s. %s' % (directory, e.strerror))
