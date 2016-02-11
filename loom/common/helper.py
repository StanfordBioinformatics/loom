from datetime import datetime
import time

def wait_for_true(test_method, timeout_seconds=20, sleep_interval=None):
    if sleep_interval == None:
        sleep_interval = timeout_seconds/10.0
    start_time = datetime.now()
    while not test_method():
        time.sleep(sleep_interval)
        time_running = datetime.now() - start_time
        if time_running.seconds > timeout_seconds:
            raise Exception("Timeout")
