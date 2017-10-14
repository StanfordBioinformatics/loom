#!/bin/bash

# Requires pip

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
version=$(cat $DIR/../VERSION)

if [ "$version" = "" ]; then
    echo Error: Version not found in $DIR/../VERSION
    exit 1;
fi

echo Found version \"$version\" in ../VERSION
echo Installing packages

for component in utils server worker
do
    pip install -U -e $DIR/../loomengine_$component/
done
pip install -U -e $DIR/../loomengine/
