#!/bin/bash
cmd_path=$(dirname $0)
echo $cmd_path
cd "$cmd_path"

target=$1

cd ..
if [ "$target" == "tar.gz" ]
then
    echo "pack tar.gz package"
    tar cvzf ./multiple_actions_without_venv.tar.gz multiple_actions_without_venv
else
    echo "pack zip package"
    zip -r ./multiple_actions_without_venv.zip multiple_actions_without_venv
fi;
echo "end pack application"
