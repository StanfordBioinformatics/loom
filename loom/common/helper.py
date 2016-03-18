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

def get_console_logger(level=None, formatter=None, name=None):
    import logging
    import sys

    if level is None:
        level = logging.DEBUG

    if name is None:
        name = 'terminal'
        
    logger = logging.getLogger(name)
    logger.setLevel(level)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)

    if formatter is None:
        formatter = logging.Formatter('%(message)s')
        
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def get_null_logger(level=None, name=None):
    import logging
    import sys

    if level is None:
        level = logging.DEBUG

    if name is None:
        name = 'terminal'
        
    logger = logging.getLogger(name)
    logger.setLevel(level)

    ch = logging.NullHandler()
    ch.setLevel(level)

    logger.addHandler(ch)

    return logger

def on_gcloud_vm():
    """ Determines if we're running on a GCE instance."""
    import requests
    r = None
    try:
        r = requests.get('http://metadata.google.internal')
    except ConnectionError:
        return False

    try:
        if r.headers['Metadata-Flavor'] == 'Google' and r.headers['Server'] == 'Metadata Server for VM':
            return True
    except KeyError:
        return False
