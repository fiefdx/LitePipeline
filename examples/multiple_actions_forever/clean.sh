#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

echo "start clean"
rm -rf ./venvs
echo "end clean"
