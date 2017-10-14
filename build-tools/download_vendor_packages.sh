#!/bin/bash

# This must be run on all target platforms.
# e.g. macos for dev, debian jessie for Docker build

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

PACKAGES=$DIR/packages

mkdir -p $PACKAGES
pip download -d $PACKAGES -r $DIR/requirements.pip
