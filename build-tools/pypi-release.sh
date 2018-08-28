#!/bin/bash
set -e

# Requires twine, setuptools-git

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
version=$(cat $DIR/../VERSION)

if [ "$version" = "" ]; then
    echo Error: Version not found in $DIR/../VERSION
    exit 1;
fi

echo Found version \"$version\" in ../VERSION
echo Importing Loom packages to pypi

for component in utils server worker
do
    twine upload $DIR/../$component/dist/loomengine_$component-$version.tar.gz
done
twine upload $DIR/../client/dist/loomengine-$version.tar.gz
