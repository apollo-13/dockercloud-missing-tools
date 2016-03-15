#!/bin/bash

BUILD_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_TARGET=$BUILD_DIRECTORY/terminate-unreachable-nodes.zip

cd $BUILD_DIRECTORY
rm -rf tmp
rm -f $BUILD_TARGET
virtualenv tmp
source tmp/bin/activate
pip install python-dockercloud
zip -9 $BUILD_TARGET terminate-unreachable-nodes.py
cd tmp/lib/python2.7/site-packages
zip -r9 $BUILD_TARGET *
