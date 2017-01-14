#!/bin/bash

BIN_PATH="`dirname \"$0\"`"

celery -c 30 -A loomengine.master.master -l info -P eventlet worker --workdir=${BIN_PATH}/../loomengine/master --without-gossip
# omitting --without-gossip causes missed heartbeat errors
