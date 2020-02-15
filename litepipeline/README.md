# LitePipeline

A distributed pipeline system, based on Python3, tornado, venv-pack, pyinstaller.

All code based on Python3, do not use Python2!

It still under development, so, maybe have some bugs or not stable enough!

See more details at https://github.com/fiefdx/LitePipeline

# Install
```bash
# install from pip
$ pip3 install -U litepipeline
# or install from source code
$ cd ./litepipeline
$ python3 ./setup.py install

# this will install 4 commands: liteconfig, litemanager, litenode, litepipeline
# liteconfig: to generate manager's or node's configuration file
# litemanager: to start LitePipeline manager
# litenode: to start LitePipeline node
# litepipeline: command line tool to communicate with LitePipeline cluster
```

# run

## Run Manager
```bash
# create manager's data directory
$ mkdir ./manager_data

# generate manager's configuration file
$ cd ./manager_data
# this will generate a configuration.yml file under ./manager_data
$ liteconfig -s manager -o ./

# run manager
$ litemanager -c ./configuration.yml

# test
$ curl localhost:8000
# return this message
{"message": "LitePipeline manager service"}
```

## Run Node
```bash
# create node's data directory
$ mkdir ./node_data

# generate node's configuration file
$ cd ./node_data
# this will generate a configuration.yml file under ./node_data
$ liteconfig -s node -o ./

# run node
# after start node, node will register to manager, and get a unique node id
$ litenode -c ./configuration.yml

# test
$ curl localhost:8001
# return this message
{"message": "LitePipeline node service"}
```

## Communicate with LitePipeline cluster
```bash
$ litepipeline localhost:8000 cluster info
# | node_id                              | http_host | http_port | action_slots | app_path                                                 | data_path                     
1 | 32313239-e7ee-4f90-8c05-4e08fb48be70 | 127.0.0.1 | 8001      | 2            | /usr/local/lib/python3.7/dist-packages/litepipeline/node | /home/pi/Develop/litenode/data

# use -h/--help parameter to see help message
$ litepipeline --help
usage: litepipeline [-h] [-r] [-v] address {app,task,cluster} ...

positional arguments:
  address             manager address, host:port
  {app,task,cluster}  sub-command help
    app               operate with app API
    task              operate with task API
    cluster           operate with cluster API

optional arguments:
  -h, --help          show this help message and exit
  -r, --raw           display raw json data
  -v, --version       show program's version number and exit


$ litepipeline localhost:8000 app --help
usage: litepipeline address app [-h]
                                {create,delete,update,list,info,download} ...

positional arguments:
  {create,delete,update,list,info,download}
                        sub-command app help
    create              create application
    delete              delete application
    update              update application
    list                list applications
    info                application's info
    download            download application

optional arguments:
  -h, --help            show this help message and exit


$ litepipeline localhost:8000 task --help
usage: litepipeline address task [-h] {create,delete,list,info,stop} ...

positional arguments:
  {create,delete,list,info,stop}
                        sub-command task help
    create              create task
    delete              delete task
    list                list tasks
    info                task's info
    stop                stop task

optional arguments:
  -h, --help            show this help message and exit


$ litepipeline localhost:8000 cluster --help
usage: litepipeline address cluster [-h] {info} ...

positional arguments:
  {info}      sub-command cluster help
    info      cluster's info

optional arguments:
  -h, --help  show this help message and exit

```