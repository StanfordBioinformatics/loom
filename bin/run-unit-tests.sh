#!/bin/bash
set -euxo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

loom-manage test api # server
loom test unit # client
python -m unittest discover $DIR/../utils
python -m unittest discover $DIR/../worker
