#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

echo "start clean"
rm -rf ./venvs
rm -rf ./dist
rm -rf ./build
rm -rf ./*.spec
echo "end clean"
