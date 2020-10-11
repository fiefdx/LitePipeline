# LitePipeline

A lightweight, scalable, distributed pipeline system, based on Python3, tornado, venv-pack, pyinstaller.

All code based on Python3, do not use Python2!

It still under development, so, maybe have some bugs or not stable enough!

You can use LitePipeline with LiteDFS, a distributed file system, based on Python3, tornado, inspired by HDFS.

See LiteDFS at https://github.com/fiefdx/LiteDFS

See more details at https://github.com/fiefdx/LitePipeline

# Install
```bash
# install from pip
$ pip3 install -U litepipeline
# or install from source code
$ cd ./litepipeline
$ python3 ./setup.py install

# this will install 5 commands: liteconfig, litemanager, litenode, litepipeline, liteviewer
# liteconfig: to generate manager's or node's configuration file
# litemanager: to start LitePipeline manager
# litenode: to start LitePipeline node
# litepipeline: command line tool to communicate with LitePipeline cluster
# liteviewer: the web UI service, for communicate with LitePipeline cluster with web browser.
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

## Run Viewer
```bash
# create viewer's data directory
$ mkdir ./viewer_data

# generate viewer's configuration file
$ cd ./viewer_data
# this will generate a configuration.yml file and other scripts under ./viewer_data
$ liteconfig -s viewer -o ./

# run viewer
$ liteviewer -c ./configuration.yml

# test
# use web browser open: http://localhost:8088
```

## Use Web Browser Communicate With LitePipeline Cluster

Use web browser open the liteviewer's host & port in it's configuration file

## Use Command Line Communicate With LitePipeline Cluster
```bash
$ litepipeline localhost:8000 cluster info
# | node_id                              | http_host | http_port | action_slots | app_path                                                 | data_path                     
1 | 32313239-e7ee-4f90-8c05-4e08fb48be70 | 127.0.0.1 | 8001      | 2            | /usr/local/lib/python3.7/dist-packages/litepipeline/node | /home/pi/Develop/litenode/data

# use -h/--help parameter to see help message
$ litepipeline --help
usage: litepipeline [-h] [-W COLUMN_WIDTH] [-v]
                    address
                    {app,app_history,task,cluster,workspace,workflow,work,schedule,service}
                    ...

positional arguments:
  address               manager address, host:port
  {app,app_history,task,cluster,workspace,workflow,work,schedule,service}
                        sub-command help
    app                 operate with app API
    app_history         operate with app_history API
    task                operate with task API
    cluster             operate with cluster API
    workspace           operate with workspace API
    workflow            operate with workflow API
    work                operate with work API
    schedule            operate with schedule API
    service             operate with service API

optional arguments:
  -h, --help            show this help message and exit
  -W COLUMN_WIDTH, --column_width COLUMN_WIDTH
                        column max width
  -v, --version         show program's version number and exit


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
usage: litepipeline address task [-h]
                                 {create,delete,list,info,rerun,recover,stop}
                                 ...

positional arguments:
  {create,delete,list,info,rerun,recover,stop}
                        sub-command task help
    create              create task
    delete              delete task
    list                list tasks
    info                task's info
    rerun               rerun task
    recover             recover task
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