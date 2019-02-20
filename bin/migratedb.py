#!/usr/bin/env python

import argparse
import os
import re
import subprocess

def get_parser():
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument(
        '-s', '--skip-if-initialized',
        action='store_true',
        help='Do not apply migrations if database is already initialized')
    return parser

def get_args():
    parser = get_parser()
    return parser.parse_args()

def migrate(skip_if_initialized=True):
    bin_path = os.path.dirname(os.path.abspath(__file__))
    manage_executable = 'loom-manage'

    p = subprocess.Popen([manage_executable, 'showmigrations'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.wait()
    if p.returncode != 0:
        raise SystemExit('showmigrations command failed with this output:\n "%s"' % p.stdout.read())
    # stdout looks something like this:
    #
    # api
    #  [X] 0001_initial
    # auth
    #  [X] 0001_initial
    #  [X] 0002_alter_permission_name_max_length
    #  [ ] 0003_alter_user_email_max_length
    #  [ ] 0004_alter_user_username_opts
    # ...
    text = p.stdout.read()
    pending_migrations = len(re.findall('\[ \]', text))
    completed_migrations = len(re.findall('\[X\]', text))
    total_migrations = pending_migrations + completed_migrations

    if total_migrations == 0:
        raise SystemExit('No migrations found')
    if pending_migrations == 0:
        print "No migrations pending"
        return
    if skip_if_initialized and completed_migrations > 0:
        print "Skipping %s pending migrations" % pending_migrations
        return
    p = subprocess.Popen([manage_executable, 'migrate'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.wait()
    if p.returncode != 0:
        raise SystemExit(
            'migratedb command failed with this output:\n "%s"' % p.stdout.read())
    text = p.stdout.read()
    print text

if __name__=='__main__':
    args = get_args()
    migrate(skip_if_initialized=args.skip_if_initialized)
