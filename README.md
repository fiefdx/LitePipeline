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

## Install LitePipeline
```bash
# this will install 4 commands: litepipeline, litemanager, litenode, liteconfig
$ pip3 install litepipeline
```

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

## Try Example Application

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
# | app_id                               | result | message
1 | daf41830-c2f9-4b68-8890-7dc286a7ac12 | ok     |

# list actions
$ litepipeline localhost:8000 app list
 # | application_id                       | name                                 | create_at                  | update_at
 1 | daf41830-c2f9-4b68-8890-7dc286a7ac12 | multiple actions demo                | 2020-01-16 22:44:10.886778 | 2020-01-16 22:44:10.886778

# create task
$ litepipeline localhost:8000 task create -a "daf41830-c2f9-4b68-8890-7dc286a7ac12" -n "task demo"
# | task_id                              | result | message
1 | 0d50caed-760b-40a5-bcc7-dcdb46960675 | ok     |

# get task status
# running
$ litepipeline localhost:8000 task info -t 0d50caed-760b-40a5-bcc7-dcdb46960675
# | task_id                              | application_id                       | task_name | create_at                  | start_at                   | end_at | stage   | status
1 | 0d50caed-760b-40a5-bcc7-dcdb46960675 | daf41830-c2f9-4b68-8890-7dc286a7ac12 | task demo | 2020-01-16 22:47:39.910642 | 2020-01-16 22:47:40.792083 | None   | running | None

# running raw result
$ litepipeline -r localhost:8000 task info -t 0d50caed-760b-40a5-bcc7-dcdb46960675
{
    "result": "ok",
    "task_info": {
        "application_id": "daf41830-c2f9-4b68-8890-7dc286a7ac12",
        "create_at": "2020-01-16 22:47:39.910642",
        "end_at": null,
        "id": 58,
        "input_data": {},
        "result": {},
        "stage": "running",
        "start_at": "2020-01-16 22:47:40.792083",
        "status": null,
        "task_id": "0d50caed-760b-40a5-bcc7-dcdb46960675",
        "task_name": "task demo",
        "update_at": "2020-01-16 22:47:40.792184"
    },
    "task_running_info": [
        {
            "app_id": "daf41830-c2f9-4b68-8890-7dc286a7ac12",
            "app_sha1": "6e16103b61b81d034932062da8bd4d1b690db04b",
            "condition": [],
            "env": "venvs/venv",
            "input_data": {},
            "main": "python first.py",
            "name": "first",
            "node": "127.0.0.1:8001",
            "node_id": "53702ac7-7e68-4926-9dcc-66007a4aea9e",
            "task_id": "0d50caed-760b-40a5-bcc7-dcdb46960675"
        },
        {
            "app_id": "daf41830-c2f9-4b68-8890-7dc286a7ac12",
            "app_sha1": "6e16103b61b81d034932062da8bd4d1b690db04b",
            "condition": [],
            "env": "venvs/venv",
            "input_data": {},
            "main": "python second.py",
            "name": "second",
            "node": "127.0.0.1:8001",
            "node_id": "53702ac7-7e68-4926-9dcc-66007a4aea9e",
            "task_id": "0d50caed-760b-40a5-bcc7-dcdb46960675"
        }
    ]
}

# finished
$ litepipeline localhost:8000 task info -t 0d50caed-760b-40a5-bcc7-dcdb46960675
# | task_id                              | application_id                       | task_name | create_at                  | start_at                   | end_at                     | stage    | status
1 | 0d50caed-760b-40a5-bcc7-dcdb46960675 | daf41830-c2f9-4b68-8890-7dc286a7ac12 | task demo | 2020-01-16 22:47:39.910642 | 2020-01-16 22:47:40.792083 | 2020-01-16 22:49:50.104178 | finished | success
```
