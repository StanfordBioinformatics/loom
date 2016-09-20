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
