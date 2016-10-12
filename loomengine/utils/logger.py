import logging
import os
import sys
from .helper import init_directory

LEVELS = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    Credit to: http://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip()) 

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

def _get_file_handler(log_file, log_level):
    init_directory(os.path.abspath(os.path.dirname(log_file)))
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(
        logging.Formatter('%(levelname)s [%(asctime)s] %(message)s'))
    return file_handler

def get_file_logger(name, log_level_string, log_file, log_stdout_stderr=False):
    log_level = LEVELS[log_level_string.upper()]
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(_get_file_handler(log_file, log_level))
    if log_stdout_stderr:
        # Route stdout and stderr to logger
        stdout_logger = StreamToLogger(logger, logging.INFO)
        sys.stdout = stdout_logger
        stderr_logger = StreamToLogger(logger, logging.ERROR)
        sys.stderr = stderr_logger
    return logger

def get_stdout_logger(name, log_level_string):
    log_level = LEVELS[log_level_string.upper()]
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    logger.addHandler(stream_handler)
    return logger
