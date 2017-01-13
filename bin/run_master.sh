#!/bin/bash

DEFAULT_LOG_LEVEL=info
DEFAULT_SOCKET=0.0.0.0:8000

LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
LOOM_MASTER_SOCKET=${LOOM_MASTER_SOCKET:-$DEFAULT_SOCKET}

gunicorn loomengine.master.master.wsgi --bind ${LOOM_MASTER_SOCKET} --log-level ${LOG_LEVEL} --capture-output
