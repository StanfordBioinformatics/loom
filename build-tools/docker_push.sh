#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
version=$(cat $DIR/../VERSION)

if [ "$version" = "" ]; then
    echo Error: Version not found in $DIR/../VERSION
    exit 1;
fi

echo Found version \"$version\" in ../VERSION

docker push loomengine/loom:$version
