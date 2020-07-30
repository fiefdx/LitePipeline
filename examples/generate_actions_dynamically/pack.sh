#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

target=$1

echo "start create venv"
mkdir ./venvs
cd ./venvs
python3 -m venv --copies ./venv
. ./venv/bin/activate
cd ..
python -m pip install --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r ./requirements.txt
# python -m pip install -r ./requirements.txt
cd ./venvs
python -m venv_pack
deactivate
rm -rf ./venv
echo "end create venv"

echo "start pack application"
cd ../..
if [ "$target" == "tar.gz" ]
then
    echo "pack tar.gz package"
    tar cvzf ./generate_actions_dynamically.tar.gz generate_actions_dynamically
else
    echo "pack zip package"
    zip -r ./generate_actions_dynamically.zip generate_actions_dynamically
fi;
echo "end pack application"
