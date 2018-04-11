#!/bin/bash
set -e

# Requires pip

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
version=$(cat $THISDIR/../VERSION)

if [ "$version" = "" ]; then
    echo Error: Version not found in $THISDIR/../VERSION
    exit 1;
fi

echo Found version \"$version\" in ../VERSION
echo Installing Loom packages

for component in utils server worker
do
    pip install -U $THISDIR/../$component/dist/loomengine_$component-$version.tar.gz
done
pip install -U $THISDIR/../client/dist/loomengine-$version.tar.gz
