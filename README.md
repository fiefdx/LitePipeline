# LitePipeline

A distributed pipeline system, based on Python3, tornado, venv-pack, pyinstaller.

All code based on Python3, do not use Python2!

It still under development, so, maybe have some bugs or not stable enough!

# Conceptions

1. manager: the central node of the cluster, manage all deployed applications, moniter tasks's status.

2. node: the worker node of the cluster, execute task's action, update action's result/status to manager.

3. client(litepipeline): the command line tool for communicate with the cluster.

4. examples: a few demo applications.

5. application: a tarball of python scripts, include python scripts/actions, configuration file, venv tarball.

6. action: application can include multiple scripts, every script is an action, action is the smallest unit to be executed by node, every action/script input with workspace a directory for store temporary data, when action execute, input.data file the script input json file will be in the workspace, and after action execute, it may generate a output.data file the script output json file in the workspace.

7. task: task include application id and input data, after task be created, manager will process task one by one, delivery executable actions to node with relative input data.

# Deployment

## Run Manager

### Configuration
```yaml
log_level: NOSET            # NOSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
log_path: ./logs            # log file directory
http_host: 0.0.0.0          # manager's http host
http_port: 8000             # manager's http port
tcp_host: 0.0.0.0           # manager's tcp host
tcp_port: 6001              # manager's tcp port
max_buffer_size: 1073741824 # 1073741824 = 1G, tornado body size limit, affect application tarball size
scheduler_interval: 1       # the scheduler service interval, 1 second
data_path: ./data           # manager data store directory
```

### Run
```bash
# install tornado_discovery package
# download it from github https://github.com/fiefdx/tornado_discovery
$ tar xzvf ./tornado_discovery.tar.gz or unzip ./tornado_discovery.zip
$ cd tornado_discovery
$ sudo python3 ./setup.py install

# install dependencies
$ cd ./manager
$ sudo pip3 install -r ./requirement.txt

# run manager
$ python3 ./Manager.py

# test
$ curl localhost:8000
# return this message
{"message": "LitePipeline manager service"}
```

## Run Node

### Configuration
```yaml
log_level: NOSET              # NOSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
log_path: ./logs              # log file directory
http_host: 0.0.0.0            # node's http host
http_port: 8001               # node's http port
manager_http_host: 127.0.0.1  # manager's http host
manager_http_port: 8000       # manager's http port
manager_tcp_host: 127.0.0.1   # manager's tcp host
manager_tcp_port: 6001        # manager's tcp port
heartbeat_interval: 1         # heartbeat interval, 1 seconds
heartbeat_timeout: 30         # heartbeat timeout, 30 seconds
retry_interval: 5             # retry to connect manager interval, when lost connection, 5 seconds
executor_interval: 1          # the scheduler service interval, 1 second
action_slots: 2               # how many actions can be executed parallelly
data_path: ./data             # manager data store directory         
```

### Run
```bash
# install tornado_discovery package
# download it from github https://github.com/fiefdx/tornado_discovery
$ tar xzvf ./tornado_discovery.tar.gz or unzip ./tornado_discovery.zip
$ cd tornado_discovery
$ sudo python3 ./setup.py install

# install dependencies
$ cd ./node
$ sudo pip3 install -r ./requirement.txt

# run node
# after start node, node will register to manager, and get a unique node id
$ python3 ./Node.py

# test
$ curl localhost:8001
# return this message
{"message": "LitePipeline node service"}
```

## Try Example Application

### Install Command Line Tool
```bash
$ cd ./client
$ python3 ./setup.py install
```

### Pack Application

1. if you use python3 venv to pack application, the venv's python version should be the same to node's python3 version, otherwise, package like numpy may not work.

2. if you use pyinstaller to pack application, the venv's python version should be the same or lower to node's python3 version, otherwise, it maybe not work.

```bash
$ cd ./examples
# run pack script, it will generate multiple_actions.tar.gz tarball
$ ./multiple_actions/pack.sh
```

### Run A Task
```bash
# create application
$ litepipeline localhost:8000 app create -f ./mulitple_actions.tar.gz -n "multiple actions demo" -d "demo"
********** litepipeline command line tool **********
{
    "result": "ok",
    "app_id": "bb303d82-3747-4a18-b9fd-80ca4b913a3f"
}

# list actions
$ litepipeline localhost:8000 app list
********** litepipeline command line tool **********
{
    "result": "ok",
    "apps": [
        {
            "id": 1,
            "application_id": "bb303d82-3747-4a18-b9fd-80ca4b913a3f",
            "name": "multiple actions demo",
            "create_at": "2020-01-04 22:12:19.954319",
            "update_at": "2020-01-04 22:12:19.954319",
            "sha1": "ad8c0ffc4eb272057ee15d28b81d23b98ce8beb0",
            "description": "demo"
        }
    ]
}

# create task
$ litepipeline localhost:8000 task create -a "bb303d82-3747-4a18-b9fd-80ca4b913a3f" -n "task demo" -d "test"
********** litepipeline command line tool **********
{
    "result": "ok",
    "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98"
}

# get task status
# running
$ litepipeline localhost:8000 task info -t "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98"
********** litepipeline command line tool **********
{
    "result": "ok",
    "task_info": {
        "id": 20,
        "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98",
        "task_name": "task demo",
        "application_id": "bb303d82-3747-4a18-b9fd-80ca4b913a3f",
        "create_at": "2020-01-04 22:18:31.286750",
        "start_at": "2020-01-04 22:18:31.960786",
        "update_at": "2020-01-04 22:20:00.619223",
        "end_at": null,
        "stage": "running",
        "status": null,
        "input_data": {},
        "result": {
            "first": {
                "result": {
                    "messages": [
                        "2020-01-04 22:19:49.102217: hello world, tornado(000): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:50.106696: hello world, tornado(001): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:51.111273: hello world, tornado(002): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:52.115761: hello world, tornado(003): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:53.120362: hello world, tornado(004): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:54.124813: hello world, tornado(005): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:55.128698: hello world, tornado(006): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:56.133248: hello world, tornado(007): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:57.137671: hello world, tornado(008): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:58.142206: hello world, tornado(009): 6.0.3, numpy: 1.18.0"
                    ]
                },
                "end_at": "2020-01-04 22:20:00.445248",
                "name": "first",
                "start_at": "2020-01-04 22:19:40.428746",
                "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98",
                "stage": "finished",
                "node_id": "e3803413-a788-4255-86bb-9f40c1894dc7",
                "status": "success"
            }
        }
    },
    "task_running_info": [
        {
            "name": "second",
            "condition": [],
            "env": "venvs/venv",
            "main": "python second.py",
            "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98",
            "app_id": "bb303d82-3747-4a18-b9fd-80ca4b913a3f",
            "app_sha1": "ad8c0ffc4eb272057ee15d28b81d23b98ce8beb0",
            "input_data": {},
            "node": "192.168.199.102:8001",
            "node_id": "e3803413-a788-4255-86bb-9f40c1894dc7",
            "update_at": "2020-01-04 22:20:03.644791"
        }
    ]
}

# finished
$ litepipeline localhost:8000 task info -t "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98"
********** litepipeline command line tool **********
{
    "result": "ok",
    "task_info": {
        "id": 20,
        "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98",
        "task_name": "task demo",
        "application_id": "bb303d82-3747-4a18-b9fd-80ca4b913a3f",
        "create_at": "2020-01-04 22:18:31.286750",
        "start_at": "2020-01-04 22:18:31.960786",
        "update_at": "2020-01-04 22:20:32.587751",
        "end_at": "2020-01-04 22:20:32.587559",
        "stage": "finished",
        "status": "success",
        "input_data": {},
        "result": {
            "first": {
                "result": {
                    "messages": [
                        "2020-01-04 22:19:49.102217: hello world, tornado(000): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:50.106696: hello world, tornado(001): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:51.111273: hello world, tornado(002): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:52.115761: hello world, tornado(003): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:53.120362: hello world, tornado(004): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:54.124813: hello world, tornado(005): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:55.128698: hello world, tornado(006): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:56.133248: hello world, tornado(007): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:57.137671: hello world, tornado(008): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:58.142206: hello world, tornado(009): 6.0.3, numpy: 1.18.0"
                    ]
                },
                "end_at": "2020-01-04 22:20:00.445248",
                "name": "first",
                "start_at": "2020-01-04 22:19:40.428746",
                "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98",
                "stage": "finished",
                "node_id": "e3803413-a788-4255-86bb-9f40c1894dc7",
                "status": "success"
            },
            "second": {
                "result": {
                    "messages": [
                        "2020-01-04 22:20:04.673128: hello world, tornado(010): 6.0.3",
                        "2020-01-04 22:20:05.679347: hello world, tornado(011): 6.0.3",
                        "2020-01-04 22:20:06.689290: hello world, tornado(012): 6.0.3",
                        "2020-01-04 22:20:07.693757: hello world, tornado(013): 6.0.3",
                        "2020-01-04 22:20:08.837041: hello world, tornado(014): 6.0.3",
                        "2020-01-04 22:20:09.848112: hello world, tornado(015): 6.0.3",
                        "2020-01-04 22:20:10.852584: hello world, tornado(016): 6.0.3",
                        "2020-01-04 22:20:11.868142: hello world, tornado(017): 6.0.3",
                        "2020-01-04 22:20:12.872603: hello world, tornado(018): 6.0.3",
                        "2020-01-04 22:20:13.878179: hello world, tornado(019): 6.0.3"
                    ]
                },
                "end_at": "2020-01-04 22:20:15.456235",
                "name": "second",
                "start_at": "2020-01-04 22:20:02.824595",
                "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98",
                "stage": "finished",
                "node_id": "e3803413-a788-4255-86bb-9f40c1894dc7",
                "status": "success"
            },
            "third": {
                "result": {
                    "messages": [
                        "2020-01-04 22:19:49.102217: hello world, tornado(000): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:50.106696: hello world, tornado(001): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:51.111273: hello world, tornado(002): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:52.115761: hello world, tornado(003): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:53.120362: hello world, tornado(004): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:54.124813: hello world, tornado(005): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:55.128698: hello world, tornado(006): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:56.133248: hello world, tornado(007): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:57.137671: hello world, tornado(008): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:19:58.142206: hello world, tornado(009): 6.0.3, numpy: 1.18.0",
                        "2020-01-04 22:20:04.673128: hello world, tornado(010): 6.0.3",
                        "2020-01-04 22:20:05.679347: hello world, tornado(011): 6.0.3",
                        "2020-01-04 22:20:06.689290: hello world, tornado(012): 6.0.3",
                        "2020-01-04 22:20:07.693757: hello world, tornado(013): 6.0.3",
                        "2020-01-04 22:20:08.837041: hello world, tornado(014): 6.0.3",
                        "2020-01-04 22:20:09.848112: hello world, tornado(015): 6.0.3",
                        "2020-01-04 22:20:10.852584: hello world, tornado(016): 6.0.3",
                        "2020-01-04 22:20:11.868142: hello world, tornado(017): 6.0.3",
                        "2020-01-04 22:20:12.872603: hello world, tornado(018): 6.0.3",
                        "2020-01-04 22:20:13.878179: hello world, tornado(019): 6.0.3",
                        "2020-01-04 22:20:21.371127: hello world, tornado(020): 6.0.3",
                        "2020-01-04 22:20:22.375590: hello world, tornado(021): 6.0.3",
                        "2020-01-04 22:20:23.380178: hello world, tornado(022): 6.0.3",
                        "2020-01-04 22:20:24.384636: hello world, tornado(023): 6.0.3",
                        "2020-01-04 22:20:25.389135: hello world, tornado(024): 6.0.3",
                        "2020-01-04 22:20:26.393589: hello world, tornado(025): 6.0.3",
                        "2020-01-04 22:20:27.398530: hello world, tornado(026): 6.0.3",
                        "2020-01-04 22:20:28.403418: hello world, tornado(027): 6.0.3",
                        "2020-01-04 22:20:29.408097: hello world, tornado(028): 6.0.3",
                        "2020-01-04 22:20:30.413009: hello world, tornado(029): 6.0.3"
                    ]
                },
                "end_at": "2020-01-04 22:20:32.444353",
                "name": "third",
                "start_at": "2020-01-04 22:20:18.396148",
                "task_id": "b5ce2a69-d3d3-4bd4-9ce1-e7eda1fb5a98",
                "stage": "finished",
                "node_id": "e3803413-a788-4255-86bb-9f40c1894dc7",
                "status": "success"
            }
        }
    }
}
```
