import logging
import sys
import loomengine.utils

utils_logger = logging.getLogger(loomengine.utils.__name__)
utils_logger.addHandler(logging.StreamHandler(sys.stdout))
utils_logger.setLevel('INFO')
