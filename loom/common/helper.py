from datetime import datetime
import time

class Helper:

    @classmethod
    def wait_for_true(cls, test_method, timeout_seconds=20):
        start_time = datetime.now()
        while not test_method():
            time.sleep(timeout_seconds/10.0)
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")
