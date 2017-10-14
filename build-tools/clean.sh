#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Cleaning up LICENSE, VERSION, NOTICES, dist/, and *.egg.info/ in each package'"

for package_dir in $DIR/../loomengine_utils $DIR/../loomengine_worker $DIR/../loomengine_server $DIR/../loomengine

do
    echo "   $package_dir/"
    rm $package_dir/LICENSE
    rm $package_dir/NOTICES
    rm $package_dir/README.rst
    rm -r $package_dir/dist/
    rm -r $package_dir/*.egg-info/
done
