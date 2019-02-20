#!/bin/bash
set -euxo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

loom-manage test api # server
loom test unit # client
python3 -m unittest discover $DIR/../utils
python3 -m unittest discover $DIR/../worker
