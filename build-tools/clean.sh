#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Cleaning up LICENSE, VERSION, NOTICES, dist/, and *.egg.info/ in each package'"

for package_dir in $DIR/../utils $DIR/../worker $DIR/../server $DIR/../client

do
    rm $package_dir/LICENSE
    rm $package_dir/NOTICES
    rm $package_dir/README.rst
    rm -r $package_dir/dist/
    rm -r $package_dir/*.egg-info/
done
