#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

target=$1
numpy=$2
proxy=$3

echo "start create venv"
mkdir ./venvs
cd ./venvs
python3 -m venv --copies ./venv
. ./venv/bin/activate
cd ..

if [ "$numpy" == "numpy" ]
then
    python -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn Cython
    echo "install numpy from source code"
    rm -rf ./numpy
    if [ "$proxy" == "proxy" ]
    then
        export http_proxy=socks5://127.0.0.1:1086
        export https_proxy=socks5://127.0.0.1:1086
        echo "enable proxy"
    fi;
    git clone https://github.com/numpy/numpy.git
    if [ "$proxy" == "proxy" ]
    then
        unset http_proxy
        unset https_proxy
        echo "disable proxy:"
    fi;
    cd ./numpy
    python -m pip install . --no-binary :all: --no-use-pep517
    cd ..
    rm -rf ./numpy
fi;

# python -m pip install --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r ./requirements.txt
python -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple/  --trusted-host pypi.tuna.tsinghua.edu.cn -r ./requirements.txt
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
