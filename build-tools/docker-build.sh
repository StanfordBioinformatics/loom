#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
version=${1:-}

if [ -z $version ]; then
    version=${LOOM_VERSION:-}
fi

if [ -z $version ]; then
    version=$(cat $DIR/../VERSION)
fi

if [ -z $version ]; then
    echo "ERROR! No version found in args, LOOM_VERSION env var, or $DIR/../VERSION"
    exit 1
fi

echo Version set to \"$version\"
echo Building docker image loomengine/loom:$version

docker build .. -t loomengine/loom:$version
