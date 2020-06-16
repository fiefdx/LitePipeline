#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

echo "start create venv"
mkdir ./venvs
cd ./venvs
python3 -m venv --copies ./venv
. ./venv/bin/activate
cd ..
pip install --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r ./requirements.txt
# pip install -r ./requirements.txt
cd ./venvs
venv-pack
deactivate
rm -rf ./venv
echo "end create venv"

echo "start pack application"
cd ../..
tar cvzf ./multiple_actions.tar.gz multiple_actions
echo "end pack application"
