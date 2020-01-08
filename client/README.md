# litepipeline

A python3 command line tool for LitePipeline.

# install
```bash
# install from pip
$ pip3 install -U litepipeline
# or install from source code
$ cd ./client
$ python3 ./setup.py install
```

# run
```bash
# run litepipeline
$ litepipeline --help
usage: litepipeline [-h] [-a APP_ID] [-t TASK_ID] [-d DESCRIPTION] [-n NAME]
                    [-f FILE] [-o OFFSET] [-l LIMIT] [-i INPUT] [-s STAGE]
                    [-g SIGNAL] [-v]
                    address object operation

positional arguments:
  address               manager address, host:port
  object                object: [app, task, cluster]
  operation             app's operations: [create, delete, update, list, info,
                        download], task's operations: [create, delete, list,
                        info]

optional arguments:
  -h, --help            show this help message and exit
  -a APP_ID, --app_id APP_ID
                        application id
  -t TASK_ID, --task_id TASK_ID
                        task id
  -d DESCRIPTION, --description DESCRIPTION
                        application's description
  -n NAME, --name NAME  application's/task's name
  -f FILE, --file FILE  application's file
  -o OFFSET, --offset OFFSET
                        list offset
  -l LIMIT, --limit LIMIT
                        list limit
  -i INPUT, --input INPUT
                        task's input data, json string
  -s STAGE, --stage STAGE
                        task's executing stage: [pending, running, finished]
  -g SIGNAL, --signal SIGNAL
                        stop task's signal: -9 or -15
  -v, --verbosity       increase output verbosity

```