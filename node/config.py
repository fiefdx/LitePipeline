# -*- coding: utf-8 -*-
'''
Created on 2013-10-26 21:29
@summary:  import yaml configuration
@author: YangHaitao
''' 
try:
    import yaml
except ImportError:
    raise ImportError("Config module requires pyYAML package, please check if pyYAML is installed!")

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import os
#
# default config
cwd = os.path.split(os.path.realpath(__file__))[0]
configpath = os.path.join(cwd, "configuration.yml")

def update(**kwargs):
    s = open(configpath, "r")
    config = load(stream = s, Loader = Loader)
    for k in kwargs:
        if k in config:
            config[k] = kwargs[k]
    s.close()
    fp = open(configpath, "wb")
    dump(config, fp, default_flow_style = False)
    fp.close()

CONFIG = {}
try:
    # script in the app dir
    s = open(configpath, "r")
    localConf = load(stream = s, Loader = Loader)
    CONFIG.update(localConf)
    s.close()
    if "app_path" not in CONFIG:
        CONFIG["app_path"] = cwd
except Exception as e:
    print(e)

if __name__ == "__main__":
    print ("CONFIG: %s" % CONFIG)
