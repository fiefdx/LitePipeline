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
# python -m pip install --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r ./requirements.txt
python -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple/  --trusted-host pypi.tuna.tsinghua.edu.cn -r ./requirements.txt
# python -m pip install -r ./requirements.txt
echo "end create venv"

echo "start pack application"
python -m PyInstaller -F ./first.py
python -m PyInstaller -F ./second.py 
python -m PyInstaller -F ./third.py
cp ./configuration.json ./dist/
deactivate
rm -rf ./build
cd ..
if [ "$target" == "tar.gz" ]
then
    echo "pack tar.gz package"
    tar -C ./multiple_actions_pyinstaller cvzf ./multiple_actions_pyinstaller.tar.gz dist
else
    echo "pack zip package"
    cd ./multiple_actions_pyinstaller
    zip -r ../multiple_actions_pyinstaller.zip dist

fi;
echo "end pack application"
