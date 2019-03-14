import ConfigParser
import dateutil.parser
import dateutil.tz
import logging
import os
import sys
import loomengine_utils
from StringIO import StringIO

logging.basicConfig(level=logging.INFO, format='%(message)s')


class LoomClientError(Exception):
    pass


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
        raise LoomClientError('Could not parse "%s" as boolean. '
                         'Use true|yes|on|1 or false|no|off|0.' % value)


def to_list(value):
    if isinstance(value, list):
        return value
    return value.strip(',').split(',')


def parse_settings_file(settings_file):
    # dummy section name because ConfigParser requires at least one section
    PARSER_SECTION = 'settings'
    parser = ConfigParser.SafeConfigParser()
    # Do not transform settings names
    parser.optionxform = str
    try:
        with open(settings_file) as stream:
            # Add a section, since ConfigParser requires it
            stream = StringIO("[%s]\n" % PARSER_SECTION + stream.read())
            parser.readfp(stream)
    except IOError:
        raise SystemExit(
            'ERROR! Could not open file to read settings at "%s".'
            % settings_file)
    except ConfigParser.ParsingError as e:
        raise SystemExit(
            'ERROR! Could not parse settings in file "%s".\n %s'
            % (settings_file, e.message))
    if parser.sections() != [PARSER_SECTION]:
        raise SystemExit(
            'ERROR! Found extra sections in settings file: "%s". '
            'Sections are not needed.' % parser.sections())
    raw_settings = dict(parser.items(PARSER_SECTION))
    settings = {}
    for key, value in raw_settings.items():
        settings[key] = value
    return settings


def write_settings_file(settings_file, settings):
    with open(settings_file, 'w') as f:
        for key, value in sorted(settings.items()):
            f.write('%s=%s\n' % (key, value))
