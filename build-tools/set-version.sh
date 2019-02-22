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
# as required by PyPi.
# We also allow alphanumeric strings to support using git commit versions in development builds.
N=\[0-9\]+
PEP440_VERSION="${N}(\.${N})*((a|b|rc)${N}|\.(post|dev)${N})?"
if [[ ! "$version" =~ ^${PEP440_VERSION}$ ]]; then
    echo "WARNING! Invalid version \"$version\" does not follow PEP 440. See https://www.python.org/dev/peps/pep-0440/#public-version-identifiers"
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo Updating version to \"$version\"

echo "    updating $DIR/../VERSION"
echo $version > $DIR/../VERSION

for package_dir in $DIR/../utils/loomengine_utils $DIR/../worker/loomengine_worker $DIR/../server/loomengine_server $DIR/../client/loomengine

do
    echo "    updating $package_dir/VERSION"
    echo $version > $package_dir/VERSION
done
