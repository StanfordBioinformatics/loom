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

for package in loomengine loomengine_server loomengine_worker loomengine_utils
do
    pip uninstall -y $package
done
