#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

echo "start create venv"
mkdir ./venvs
cd ./venvs
python3 -m venv --copies ./venv
. ./venv/bin/activate
cd ..
python -m pip install --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r ./requirements.txt
# python -m pip install -r ./requirements.txt
echo "end create venv"

echo "start pack application"
python -m PyInstaller -F ./first.py
python -m PyInstaller -F ./second.py 
python -m PyInstaller -F ./third.py
cp ./configuration.json ./dist/
tar cvzf ../multiple_actions_pyinstaller.tar.gz dist
rm -rf ./build
deactivate
echo "end pack application"
