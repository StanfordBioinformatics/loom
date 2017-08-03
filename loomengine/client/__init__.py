import logging
import sys
import loomengine.utils

utils_logger = logging.getLogger(loomengine.utils.__name__)
utils_logger.addHandler(logging.StreamHandler(sys.stdout))
utils_logger.setLevel('INFO')

_DATETIME_FORMAT = '%b %d, %Y %-I:%M:%S %p'

def _render_time(timestr):
    time_gmt = dateutil.parser.parse(timestr)
    time_local = time_gmt.astimezone(tz.tzlocal())
    return format(time_local, _DATETIME_FORMAT)
