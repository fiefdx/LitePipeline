# LitePipeline Pack Tool

This is a tool for pack & deploy application on LitePipeline Cluster

# Install
```bash
# install from pip
$ pip3 install -U litepipeline_pack_tool
# or install from source code
$ cd ./litepipeline_pack_tool
$ python3 ./setup.py install

# this will install 1 command: litepack
```

## Usage
```bash
$ litepack --help
usage: litepack [-h] -P LITEPIPELINE -p PACK_APP_ID -o {pack,create,update}
                [-a APP_ID] -i INPUT [-f {tar.gz,zip}] [-n NAME]
                [-d DESCRIPTION] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -P LITEPIPELINE, --litepipeline LITEPIPELINE
                        litepipeline manager node's host:port
  -p PACK_APP_ID, --pack_app_id PACK_APP_ID
                        pack application id
  -o {pack,create,update}, --operate {pack,create,update}
                        operate
  -a APP_ID, --app_id APP_ID
                        application's id, which will be updated
  -i INPUT, --input INPUT
                        local application's source code root directory
  -f {tar.gz,zip}, --format {tar.gz,zip}
                        output package format
  -n NAME, --name NAME  application's name
  -d DESCRIPTION, --description DESCRIPTION
                        application's description
  -v, --version         show program's version number and exit

# pack and download application
$ litepack -P 192.168.199.149:8000 -p f584e7f3-ec24-4d72-a866-2854ca5a9d62 -o pack -i /home/pi/Develop/LitePipeline/examples/pack_application_with_ldfs -f zip

# pack, download application and create application on LitePipeline
$ litepack -P 192.168.199.149:8000 -p f584e7f3-ec24-4d72-a866-2854ca5a9d62 -o create -n test_app -d test_description -i /home/pi/Develop/LitePipeline/examples/pack_application_with_ldfs -f zip

# pack, download application and update application on LitePipeline
$ litepack -P 192.168.199.149:8000 -p f584e7f3-ec24-4d72-a866-2854ca5a9d62 -o update -a a96a2b98-cb0f-4139-a6a9-f36e105ec1d8 -i /home/pi/Develop/LitePipeline/examples/pack_application_with_ldfs -f zip
```