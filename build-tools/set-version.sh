#!/bin/bash
set -euxo pipefail

# Usage:
# ./set_version.sh VERSION


version=${1:-}

if [ -z $version ]; then
    version=${LOOM_VERSION:-}
fi

if [ -z $version ]; then
    version=0.0.0.dev0
    echo "WARNING! Setting version to default \"0.0.0.dev0\". Set the LOOM_VERSION env var or provide a command line argument"
fi

# Make sure version is something like 1.2.3, 1.2a1, 0.1.2.post3, etc.
# as required by PyPi
N=\[0-9\]+
PEP440_VERSION="${N}(\.${N})*((a|b|rc)${N}|\.(post|dev)${N})?"
if [[ ! "$version" =~ ^${PEP440_VERSION}$ ]]; then
    echo "ERROR! Invalid version" $version "does not follow PEP 440. See https://www.python.org/dev/peps/pep-0440/#public-version-identifiers"
    exit 1
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
