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