#!/bin/bash
set -e

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

for package_dir in $DIR/../utils $DIR/../worker $DIR/../server $DIR/../client

do
    echo "   $package_dir/"
    cp ../LICENSE $package_dir/LICENSE
    cp ../NOTICES $package_dir/NOTICES
    cp ../README.rst $package_dir/README.rst
done

for package in $DIR/../utils $DIR/../server $DIR/../client $DIR/../worker
do
    echo "$(cd $package; python setup.py sdist;)"
done
