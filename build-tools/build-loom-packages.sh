#!/bin/bash
set -euxo pipefail

# Requires these python packages to be installed:
# * setuptools-git
# * twine

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -f $THISDIR/../VERSION ]; then
    echo ERROR! Aborting because VERSION is not set. \
         First run ${THISDIR}/set-version.sh
    exit 1
fi

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
