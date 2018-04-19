#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Cleaning up LICENSE, VERSION, NOTICES, dist/, and *.egg.info/ in each package'"

for package_dir in $DIR/../utils $DIR/../worker $DIR/../server $DIR/../client

do
    rm -f $package_dir/VERSION
    rm -f $package_dir/LICENSE
    rm -f $package_dir/NOTICES
    rm -f $package_dir/README.rst
    rm -rf $package_dir/dist/
    rm -rf $package_dir/*.egg-info/
done

echo "Removing $DIR/../VERSION"
rm -f $DIR/../VERSION
