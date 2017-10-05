#!/bin/bash

DEFAULT_LOG_LEVEL=info
DEFAULT_IP=0.0.0.0
DEFAULT_PORT=8000
DEFAULT_GUNICORN_WORKERS_COUNT=10
DEFAULT_FORCE_DB_MIGRATIONS_ON_START=false

LOOM_LOG_LEVEL=${LOOM_LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
LOOM_MASTER_INTERNAL_IP=${LOOM_MASTER_INTERNAL_IP:-$DEFAULT_IP}
LOOM_MASTER_INTERNAL_PORT=${LOOM_MASTER_INTERNAL_PORT:-$DEFAULT_PORT}
LOOM_MASTER_GUNICORN_WORKERS_COUNT=${LOOM_MASTER_GUNICORN_WORKERS_COUNT:-$DEFAULT_GUNICORN_WORKERS_COUNT}
FORCE_DB_MIGRATIONS_ON_START=${LOOM_FORCE_DB_MIGRATIONS_ON_START:-$DEFAULT_FORCE_DB_MIGRATIONS_ON_START}

for item in true TRUE True t T yes YES Yes y Y
do
    if [ "$FORCE_MIGRATEDB_ON_START" == "$item" ]; then
        FORCE_DB_MIGRATIONS_ON_START=true
        break
    fi
done

BIN_PATH="`dirname \"$0\"`"

# Wait for database to become available
RETRIES=10
n=0
while :
do
    # break if db connection is successful
    $BIN_PATH/../loomengine/master/manage.py inspectdb > /dev/null 2>&1 && break

    # exit if retries exceeded
    if [ $n -ge $RETRIES ]
    then
	>&2 echo "Timeout while waiting for database"
	exit 1;
    fi
    sleep 5
    n=$[$n+1]
    echo "Could not reach database. Retry $n/$RETRIES."
done

if [ "$FORCE_DB_MIGRATIONS_ON_START" == "true" ]; then
    echo "Applying database migrations"
    python $BIN_PATH/migratedb.py
else
    echo "Verifying that database is initialized"
    python $BIN_PATH/migratedb.py --skip-if-initialized
fi

gunicorn loomengine.master.master.wsgi --bind ${LOOM_MASTER_INTERNAL_IP}:${LOOM_MASTER_INTERNAL_PORT} --log-level ${LOOM_LOG_LEVEL} --capture-output -w ${LOOM_MASTER_GUNICORN_WORKERS_COUNT} --timeout 300
