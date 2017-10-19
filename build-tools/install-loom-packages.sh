#!/bin/bash
set -e

# Requires pip

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
version=$(cat $DIR/../VERSION)

if [ "$version" = "" ]; then
    echo Error: Version not found in $DIR/../VERSION
    exit 1;
fi

echo Found version \"$version\" in ../VERSION
echo Installing Loom packages

for component in utils server worker
do
    pip install -U $DIR/../$component/dist/loomengine_$component-$version.tar.gz
done
pip install -U $DIR/../client/dist/loomengine-$version.tar.gz
