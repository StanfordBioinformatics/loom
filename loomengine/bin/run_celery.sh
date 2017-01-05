#!/bin/bash

BIN_PATH="`dirname \"$0\"`"

echo "CEELLLERRRYYY"

celery -c 30 -A loomengine.master.master -l info -P eventlet worker --workdir=${BIN_PATH}/../loomengine/master
