#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

echo "start create venv"
mkdir ./venvs
cd ./venvs
python3 -m venv --copies ./venv
. ./venv/bin/activate
cd ..
pip install -r ./requirements.txt
echo "end create venv"

echo "start pack application"
pyinstaller -F ./first.py
pyinstaller -F ./second.py 
pyinstaller -F ./third.py
cp ./configuration.json ./dist/
tar cvzf ../mulitple_actions_pyinstaller.tar.gz dist
rm -rf ./build
deactivate
echo "end pack application"
