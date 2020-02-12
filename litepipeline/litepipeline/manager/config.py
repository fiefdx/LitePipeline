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
import sys
import argparse
from litepipeline.version import __version__

cwd = os.path.split(os.path.realpath(__file__))[0]
parser = argparse.ArgumentParser(prog = 'litemanager')

parser.add_argument("-c", "--config", help = "configuration file path")
parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)

args = parser.parse_args()

CONFIG = {}
try:
    config_file_path = args.config
    if config_file_path and os.path.exists(config_file_path) and os.path.isfile(config_file_path):
        s = open(config_file_path, "r")
        local_config = load(stream = s, Loader = Loader)
        CONFIG.update(local_config)
        s.close()
        if "app_path" not in CONFIG:
            CONFIG["app_path"] = cwd
    else:
        parser.print_help()
        sys.exit()
except Exception as e:
    print(e)
    sys.exit()

if __name__ == "__main__":
    print ("CONFIG: %s" % CONFIG)
