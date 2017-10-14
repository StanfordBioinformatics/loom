#!/bin/bash

# Requires these python packages to be installed:
# * setuptools-git
# * twine

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
version=$(cat $DIR/../VERSION)

if [ "$version" = "" ]; then
    echo Error: Version not found in $DIR/../VERSION
    exit 1;
fi

echo Found version \"$version\" in ../VERSION
echo Copying LICENCE, NOTICES, and README.rst to all packages

for package_dir in $DIR/../loomengine_utils $DIR/../loomengine_worker $DIR/../loomengine_server $DIR/../loomengine

do
    echo "   $package_dir/"
    cp ../LICENSE $package_dir/LICENSE
    cp ../NOTICES $package_dir/NOTICES
    cp ../README.rst $package_dir/README.rst
done

for package in $DIR/../loomengine_utils $DIR/../loomengine_server $DIR/../loomengine $DIR/../loomengine_worker
do
    echo "$(cd $package; python setup.py sdist;)"
done
