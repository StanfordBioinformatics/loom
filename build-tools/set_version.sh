#!/bin/bash
set -e

# Usage:
# ./set_version.sh VERSION

if [ "$1" = "" ]; then
    echo Error: Version is required
    echo Usage: $0 VERSION
    exit 1;
fi

version=$1
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
old_version=$(cat $DIR/../VERSION)

echo Updating version from \"$old_version\" to \"$version\"
echo "    updating $DIR/../VERSION"
echo $version > $DIR/../VERSION
echo "    updating $DIR/../doc/conf.py"
sed -i.tmp "s/version = u'.*'/version = u'$version'/" ../doc/conf.py
sed -i.tmp "s/release = u'.*'/release = u'$version'/" ../doc/conf.py
rm ../doc/conf.py.tmp

for package_dir in $DIR/../utils/loomengine_utils $DIR/../worker/loomengine_worker $DIR/../server/loomengine_server $DIR/../client/loomengine

do
    echo "    updating $package_dir/VERSION"
    echo $version > $package_dir/VERSION
done
