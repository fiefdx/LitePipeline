# LitePipeline

A lightweight, scalable, distributed pipeline system, based on Python3, tornado, venv-pack, pyinstaller.

All code based on Python3, do not use Python2!, no windows support currently.

It still under development, so, maybe have some bugs or not stable enough!

You can use LitePipeline with LiteDFS, a distributed file system, based on Python3, tornado, inspired by HDFS.

See LiteDFS at https://github.com/fiefdx/LiteDFS

# Features

1. workload balance

2. support dynamically generate actions

3. scalable with add / remove node

4. lightweight, pure python implementation

5. based on venv-pack, easily deploy / update application

6. support daily timing schedule task

7. support command line and web UI interfaces

8. two level pipeline topologies, low level pipeline constructed with actions, high level pipeline constructed with applications

9. support to use docker container to run action

10. support long running & auto start service

11. support to deploy venv package separate from application package

# Conceptions

1. manager(litemanager): the central node of the cluster, manage all deployed applications, moniter tasks's status.

2. node(litenode): the worker node of the cluster, execute task's action, update action's result/status to manager.

3. client(litepipeline): the command line tool for communicate with the cluster.

4. viewer(liteviewer): the web UI service, for communicate with the cluster with web browser.

5. examples: a few demo applications.

6. venv: a tarball of python venv.

7. application: a tarball of python scripts, include python scripts/actions, configuration file, venv tarball.

8. action: application can include multiple scripts, every script is an action, action is the smallest unit to be executed by node, every action/script input with a unique workspace a directory for store action's temporary data, when action execute, input.data file the script input json file will be in the workspace, and after action executed, it may generate a output.data file the script output json file in the workspace.

9. task: task include application id and input data, after task be created, manager will process task one by one, delivery executable actions to node with relative input data.

10. workflow: just like application constructed with actions, workflow constructed with applications, you can reuse one application between workflows.

11. work: work include workflow id and input data, after work be created, manager will create tasks according to workflow's configuration.

# Deployment

## Install LitePipeline
```bash
# this will install 5 commands: litepipeline, liteviewer, litemanager, litenode, liteconfig
$ pip3 install litepipeline
```

## Run Manager

### Configuration
```yaml
log_level: NOSET                        # NOSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
log_path: /home/pi/manager_data/logs    # log file directory, can auto generate by liteconfig
http_host: 0.0.0.0                      # manager's http host
http_port: 8000                         # manager's http port
tcp_host: 0.0.0.0                       # manager's tcp host
tcp_port: 6001                          # manager's tcp port
ldfs_http_host: null                    # litedfs name node's http host
ldfs_http_port: null                    # litedfs name node's http port
max_buffer_size: 1073741824             # 1073741824 = 1G, tornado body size limit, affect application tarball size
scheduler_interval: 1                   # the scheduler service interval, 1 second
venv_store: local.tar.gz                # set where to store venv packages and what format is valid, support: local.zip, local.tar.gz, ldfs.zip, default is local.tar.gz
app_store: local.zip                    # set where to store application packages and what format is valid, support: local.zip, local.tar.gz, ldfs.zip, default is local.zip
docker_registry: null                   # local docker registry, host:port, see more about docker registry at: https://docs.docker.com/registry/
data_path: /home/pi/manager_data/data   # manager data store directory, can auto generate by liteconfig
```

### Run
```bash
# create manager's data directory
$ mkdir ./manager_data

# generate manager's configuration file
$ cd ./manager_data
# this will generate a configuration.yml file and other scripts under ./manager_data
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
log_level: NOSET                       # NOSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
log_path: /home/pi/node_data/logs      # log file directory, can auto generate by liteconfig
http_host: 0.0.0.0                     # node's http host
http_port: 8001                        # node's http port
manager_http_host: 127.0.0.1           # manager's http host
manager_http_port: 8000                # manager's http port
manager_tcp_host: 127.0.0.1            # manager's tcp host
manager_tcp_port: 6001                 # manager's tcp port
heartbeat_interval: 1                  # heartbeat interval, 1 seconds
heartbeat_timeout: 30                  # heartbeat timeout, 30 seconds
retry_interval: 5                      # retry to connect manager interval, when lost connection, 5 seconds
executor_interval: 1                   # the scheduler service interval, 1 second
action_slots: 2                        # how many actions can be executed parallelly
gpu: null                              # does this node have a GPU
docker_support: false                  # does this node support to use docker
data_path: /home/pi/node_data/data     # node data store directory, can auto generate by liteconfig
```

### Run
```bash
# create node's data directory
$ mkdir ./node_data

# generate node's configuration file
$ cd ./node_data
# this will generate a configuration.yml file and other scripts under ./node_data
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

### Configuration
```yaml
log_level: NOSET                        # NOSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
log_path: /home/pi/viewer_data/logs     # log file directory, can auto generate by liteconfig
http_host: 0.0.0.0                      # viewer's http host
http_port: 8088                         # viewer's http port
manager_http_host: 192.168.199.204      # manager's http host
manager_http_port: 8000                 # manager's http port
data_path: /home/pi/viewer_data/data    # viewer data store directory, can auto generate by liteconfig
```

### Run
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

### Web UI Screenshots

1. Cluster page
   ![Alt text](/docs/image/cluster.png?raw=true "cluster page")

2. Venv page
   ![Alt text](/docs/image/venv.png?raw=true "venv page")

3. Venv information page
   ![Alt text](/docs/image/venv_info.png?raw=true "venv info page")

4. Application page
   ![Alt text](/docs/image/application.png?raw=true "application page")

5. Application information page
   ![Alt text](/docs/image/application_info.png?raw=true "application info page")

6. Task page
   ![Alt text](/docs/image/task.png?raw=true "task page")

7. Workflow page
   ![Alt text](/docs/image/workflow.png?raw=true "workflow page")

8. Work page
   ![Alt text](/docs/image/work.png?raw=true "work page")

9. Schedule page
   ![Alt text](/docs/image/schedule.png?raw=true "schedule page")

10. Service page
   ![Alt text](/docs/image/service.png?raw=true "service page")

## Try Example Application

### Install LitePipeline Helper
```bash
$ pip3 install litepipeline_helper
```

### Application Configuration
```javascript
{
    "actions": [
        {
            "name": "first",                                       // action name
            "condition": [],                                       // execute condition, no requirement
            "docker": {                                            // optional, if action need docker to run
                "name": "python3.5.2",                             // docker image name
                "tag": "latest",                                   // docker image tag
                "args": {                                          // docker run arguments, see more detail at: https://docker-py.readthedocs.io/en/stable/containers.html
                    "cpuset_cpus": "0",
                    "mem_limit": "10m",
                    "ports": {
                        "8000/tcp": 2222
                    }
                }
            },
            "target_env": {                                        // optional, if action has some env requirement
                "platform": "x86_64",                              // node platform condition
                "docker_support": true,                            // node docker support condition
                "node_id": "e0d01ae9-5279-4a44-a772-149e7e0a0537", // node id condition
                "node_ip": "192.168.199.102"                       // node ip condition
            },
            "env": "venvs/venv",                                   // venv path or venv id(uuid4)
            "main": "python first.py"                              // execute script command 
        }, {
            "name": "second",                                      // action name
            "condition": [],                                       // execute condition, no requirement
            "env": "9c828939-3373-4af7-9127-d06e591621bd",         // venv path or venv id(uuid4)
            "main": "python second.py"                             // execute script command 
        }, {
            "name": "third",                                       // action name
            "condition": ["first", "second"],                      // execute condition, third require first's and second's results
            "env": "venvs/venv",                                   // venv path
            "main": "python third.py"                              // execute script command 
        }
    ],
    "event_actions": {                                             // optional, custom event actions, currently only support task success and fail event
        "fail": {
            "env": "venvs/venv",
            "main": "python fail.py"
        },
        "success": {
            "env": "venvs/venv",
            "main": "python success.py"
        }
    },
    "output_action": "third"                                       // this define application's output come from which action
}
```

### Action Context
```python
from litepipeline_helper.models.action import Action  # import helper class

if __name__ == "__main__":
    # start with
    workspace, input_data = Action.get_input()        # get workspace directory and input_data

    #
    # user data processing code here
    #

    # end with
    Action.set_output(data = data)                    # set output data

    # or

    # end with
    Action.set_output(data = data, actions = actions) # set output data and dynamically generated actions
```

### Workflow Configuration
```javascript
{
    "applications": [
        {
            "name": "first",                                                // name, this will be the task's name
            "condition": [],                                                // execute condition, no requirement
            "app_id": "915702d1-5e40-4c12-a1f2-fff73fa2908d",               // application id
        }, {
            "name": "second",                                               // name, this will be the task's name
            "condition": [],                                                // execute condition, no requirement
            "app_id": "915702d1-5e40-4c12-a1f2-fff73fa2908d",               // application id
        }, {
            "name": "third",                                                // name, this will be the task's name
            "condition": ["first", "second"],                               // execute condition, third require first's and second's results
            "app_id": "915702d1-5e40-4c12-a1f2-fff73fa2908d",               // application id
        }
    ],
    "event_applications": {                                                 // optional, custom event applications, currently only support work success and fail event
        "fail": {
            "app_id": "915702d1-5e40-4c12-a1f2-fff73fa2908d"
        },
        "success": {
            "app_id": "915702d1-5e40-4c12-a1f2-fff73fa2908d"
        }
    }
}
```

### Pack Application

1. if you use python3 venv to pack application, the venv's python version should be the same to node's python3 version, otherwise, package like numpy may not work.

2. if you use pyinstaller to pack application, the venv's python version should be the same or lower to node's python3 version, otherwise, it maybe not work.

```bash
$ cd ./examples
# run pack script
$ ./multiple_actions/pack.sh tar.gz # it will generate multiple_actions.tar.gz
or
$ ./multiple_actions/pack.sh zip # it will generate multiple_actions.zip 
```

### Run A Task
```bash
# create application
$ litepipeline localhost:8000 app create -f ./mulitple_actions.tar.gz -n "multiple actions demo" -d "demo"
# | app_id                               | result | message
1 | daf41830-c2f9-4b68-8890-7dc286a7ac12 | ok     |

# list applications
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
$ litepipeline localhost:8000 task info -t 0d50caed-760b-40a5-bcc7-dcdb46960675 -r
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

# download an action's workspace of a task, convenient for debugging application
$ litepipeline localhost:8000 workspace download -t 0d50caed-760b-40a5-bcc7-dcdb46960675 -n first
Packing ... \
Download from: http://localhost:8000/workspace/download?task_id=0d50caed-760b-40a5-bcc7-dcdb46960675&name=first
Downloading ... \
Workspace: ./0d50caed-760b-40a5-bcc7-dcdb46960675.first.tar.gz

# create a schedule
$ litepipeline localhost:8000 schedule create -n "every day 12:40" -a daf41830-c2f9-4b68-8890-7dc286a7ac12 -H 12 -m 40 -e true
# | schedule_id                          | result | message
1 | 111107ed-b750-4dd3-aa38-4ebce81c04f3 | ok     | 

# list schedules
$ litepipeline localhost:8000 schedule list
# | schedule_id                          | source      | source_id                            | schedule_name    | create_at                  | update_at                  | hour | minute | day_of_month | day_of_week | enable
1 | 345cb074-706f-4886-8086-ae0dc8b890a4 | application | 915702d1-5e40-4c12-a1f2-fff73fa2908d | application test | 2020-03-29 15:15:20.683066 | 2020-03-29 15:15:20.683066 | 15   | 17     | -1           | -1          | True  
2 | 708702c7-95cd-4ebd-8f1b-a5469a9f854c | workflow    | 0bf700d3-3ad2-41d5-ad12-59514d675dd5 | workflow test    | 2020-03-29 14:57:44.011059 | 2020-03-29 15:08:45.865756 | 15   | 9      | -1           | -1          | True 
```
