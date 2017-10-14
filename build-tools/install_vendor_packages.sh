#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PACKAGES=$DIR/packages

pip install --no-index --find-links=$PACKAGES -r $DIR/requirements.pip
