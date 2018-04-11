#!/bin/bash
set -e

# Requires these python packages to be installed:
# * setuptools-git
# * twine

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $THISDIR
version=$(cat $THISDIR/../VERSION)

if [ "$version" = "" ]; then
    echo Error: Version not found in $THISDIR/../VERSION
    exit 1;
fi

echo Found version \"$version\" in ../VERSION
echo Copying LICENCE, NOTICES, and README.rst to all packages

for package_dir in $THISDIR/../utils $THISDIR/../worker $THISDIR/../server $THISDIR/../client

do
    echo "   $package_dir/"
    cp $THISDIR/../LICENSE $package_dir/LICENSE
    cp $THISDIR/../NOTICES $package_dir/NOTICES
    cp $THISDIR/../README.rst $package_dir/README.rst
done

for package in $THISDIR/../utils $THISDIR/../server $THISDIR/../client $THISDIR/../worker
do
    echo "$(cd $package; python setup.py sdist;)"
done
