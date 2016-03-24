import logging
import os

def _get_handler(logfile):
    if logfile is None:
        return logging.StreamHandler()
    else:
        if not os.path.exists(os.path.dirname(logfile)):
            os.makedirs(os.path.dirname(logfile)) 
    return logging.FileHandler(logfile)

def get_logger(name, logfile=None, loglevel=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)
    formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')
    handler = _get_handler(logfile)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
