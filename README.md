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
