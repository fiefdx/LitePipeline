# LitePipeline

A distributed pipeline system, based on Python3, tornado, venv-pack, pyinstaller.

manager: the central node of the cluster, manage all deployed applications, moniter tasks's status.
node: the worker node of the cluster, execute task's action, update action's result/status to manager.
client(litepipeline): the command line tool for communicate with the cluster.
examples: a few applications example.

All code based on Python3, do not use Python2!

# Conceptions

1. application: a tarball of python scripts, include python scripts/actions, configuration file, venv tarball.

2. action: application can include multiple scripts, every script is an action, action is the smallest unit to be executed by node, every action/script input with workspace a directory for store temporary data, when action execute, input.data file the script input json file will be in the workspace, and after action execute, must have a output.data file the script output json file in the workspace.

3. task: task include application id and input data, after task be created, manager will process task one by one, delivery executable actions to node with relative input data.

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
tar xzvf ./tornado_discovery.tar.gz or unzip ./tornado_discovery.zip
cd tornado_discovery
sudo python3 ./setup.py install

# install dependencies
cd ./manager
sudo pip3 install -r ./requirement.txt

# run manager
python3 ./Manager.py

# test
curl localhost:8000
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
tar xzvf ./tornado_discovery.tar.gz or unzip ./tornado_discovery.zip
cd tornado_discovery
sudo python3 ./setup.py install

# install dependencies
cd ./node
sudo pip3 install -r ./requirement.txt

# run node
# after start node, node will register to manager, and get a unique node id
python3 ./Node.py

# test
curl localhost:8001
# return this message
{"message": "LitePipeline node service"}
```

## Try Example Application

### Install Command Line Tool
```bash
cd ./client
python3 ./setup.py install
```

### Pack Application
```bash
cd ./examples
# run pack script, it will generate multiple_actions.tar.gz tarball
./multiple_actions/pack.sh
```

### Run A Task
```bash

```
