#!/bin/bash

DEFAULT_FORCE_DB_MIGRATIONS_ON_START=false

FORCE_DB_MIGRATIONS_ON_START=${LOOM_FORCE_DB_MIGRATIONS_ON_START:-$DEFAULT_FORCE_DB_MIGRATIONS_ON_START}

for item in true TRUE True t T yes YES Yes y Y
do
    if [ "$FORCE_MIGRATEDB_ON_START" == "$item" ]; then
        FORCE_DB_MIGRATIONS_ON_START=true
        break
    fi
done

for item in true TRUE True t T yes YES Yes y Y
do
    if [ "$LOOM_LOGIN_REQUIRED" == "$item" ]; then
        LOGIN_REQUIRED=true
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
    loom-manage inspectdb > /dev/null && break

    # exit if retries exceeded
    if [ $n -ge $RETRIES ]
    then
	>&2 echo "Timeout while waiting for database"
	exit 1;
    fi
    echo "Could not reach database. Retry $n/$RETRIES in 5 seconds."
    sleep 5
    n=$[$n+1]
done

if [ "$FORCE_DB_MIGRATIONS_ON_START" == "true" ]; then
    echo "Applying database migrations"
    python $BIN_PATH/migratedb.py
else
    echo "Verifying that database is initialized"
    python $BIN_PATH/migratedb.py --skip-if-initialized
fi

if [ "$LOGIN_REQUIRED" == "true" ]; then
    echo "Creating admin user $LOOM_ADMIN_USERNAME"
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('$LOOM_ADMIN_USERNAME', '', '$LOOM_ADMIN_PASSWORD')" | loom-manage shell || true
fi
