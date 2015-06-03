#!/bin/bash

rm xppfserver/db.sqlite3
rm analyses/migrations/0*
rm immutable/migrations/0*
./manage.py makemigrations
./manage.py migrate
./manage.py syncdb
