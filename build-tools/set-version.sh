#!/bin/bash
set -e

# Usage:
# ./set_version.sh VERSION

if [ "${LOOM_VERSION}" = "" ]; then
    LOOM_VERSION=$1
fi

if [ "${LOOM_VERSION}" = "" ]; then
    echo "ERROR! No version provided. Set the LOOM_VERSION env var or provide a command line argument"
    exit 1
else
    version=${LOOM_VERSION}
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo Updating version to \"$version\"

echo "    updating $DIR/../VERSION"
echo $version > $DIR/../VERSION

if [ -f $DIR/../doc/conf.py ]; then
  echo "    updating $DIR/../doc/conf.py"
  sed -i.tmp "s/version = u'.*'/version = u'$version'/" $DIR/../doc/conf.py
  sed -i.tmp "s/release = u'.*'/release = u'$version'/" $DIR/../doc/conf.py
  rm $DIR/../doc/conf.py.tmp
else
  echo "    skipping $DIR/../doc/conf.py ... does not exist"
fi


for package_dir in $DIR/../utils/loomengine_utils $DIR/../worker/loomengine_worker $DIR/../server/loomengine_server $DIR/../client/loomengine

do
    echo "    updating $package_dir/VERSION"
    echo $version > $package_dir/VERSION
done
