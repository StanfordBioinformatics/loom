#!/bin/bash
set -euxo pipefail

# Requires pip

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -f $THISDIR/../VERSION ]; then
    echo ERROR! Aborting because VERSION is not set. \
         First run ${THISDIR}/set-version.sh
    exit 1
fi

version=$(cat $THISDIR/../VERSION)
echo Found version \"$version\" in ../VERSION
echo Installing Loom packages

for component in utils server worker
do
    if [ ! -f $THISDIR/../$component/dist/loomengine_$component-$version.tar.gz ]; then
	echo "ERROR! Aborting because package not found. First run $THISDIR/build-loom-packages.sh"
	exit 1;
    fi
done
if [ ! -f $THISDIR/../client/dist/loomengine-$version.tar.gz ]; then
    echo "ERROR! Aborting because package not found. First run $THISDIR/build-loom-packages.sh"
    exit 1;
fi

if [ ${LOOM_DEV_MODE:-} ]; then
    # Install live code, not from tarballs
    for component in utils server worker client
    do
	pip install -U -e $THISDIR/../$component/
    done
else
    # Install from distributable tarballs
    for component in utils server worker
    do
	pip install -U $THISDIR/../$component/dist/loomengine_$component-$version.tar.gz
    done
    pip install -U $THISDIR/../client/dist/loomengine-$version.tar.gz
fi

