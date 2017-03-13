#!/bin/bash

BIN_PATH="`dirname \"$0\"`"

DEFAULT_LOG_LEVEL=info

LOOM_LOG_LEVEL=${LOOM_LOG_LEVEL:-$DEFAULT_LOG_LEVEL}

# omitting --without-gossip causes missed heartbeat errors
celery beat -A loomengine.master.master -l ${LOOM_LOG_LEVEL} --workdir=${BIN_PATH}/../loomengine/master


