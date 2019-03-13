import dateutil.parser
import dateutil.tz
import logging
import sys
import loomengine_utils

utils_logger = logging.getLogger(loomengine_utils.__name__)
utils_logger.addHandler(logging.StreamHandler(sys.stdout))
utils_logger.setLevel('INFO')

_DATETIME_FORMAT = '%b %d, %Y %-I:%M:%S %p'


def _render_time(timestr):
    time_gmt = dateutil.parser.parse(timestr)
    time_local = time_gmt.astimezone(dateutil.tz.tzlocal())
    return format(time_local, _DATETIME_FORMAT)


def to_bool(value):
    if value and value.lower() in ['true', 'yes', 'on', '1']:
        return True
    elif value and value.lower() in ['false', 'no', 'off', '0']:
        return False
    else:
        raise ValueError('Could not parse "%s" as boolean. '
                         'Use true|yes|on|1 or false|no|off|0.' % value)

def to_list(value):
    if isinstance(value, list):
        return value
    return value.strip(',').split(',')
