# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import datetime
from pathlib import Path

import tornado
import numpy

import logger

LOG = logging.getLogger(__name__)

home = str(Path.home())


if __name__ == "__main__":
    print("argv: %s" % sys.argv)
    if len(sys.argv) < 2:
        print("need workspace argument")
    else:
        workspace = sys.argv[1]
        logs_directory = os.path.join(workspace, "logs")
        fp = open(os.path.join(workspace, "input.data"), "r")
        input_data = json.loads(fp.read())
        fp.close()

        logger.config_logging(file_name = "first.log",
                              log_level = "DEBUG",
                              dir_name = logs_directory,
                              day_rotate = False,
                              when = "D",
                              interval = 1,
                              max_size = 20,
                              backup_count = 5,
                              console = False)
        LOG.debug("test start")
        LOG.debug("input_data: %s", input_data)

        fp = open(os.path.join(workspace, "output.data"), "w")
        data = {"actions": []}
        for a in range(5):
            action = {
                "name": "second_%03d" % a,
                "condition": [],
                "env": "venvs/venv",
                "main": "python second.py",
                "input_data": {"messages": []},
                "next": "third",
            }
            for i in range(2):
                now = datetime.datetime.now()
                message = "%s: hello world, tornado(%03d, %03d): %s, numpy: %s" % (now, a, i, tornado.version, numpy.__version__)
                action["input_data"]["messages"].append(message)
                LOG.debug(message)
                time.sleep(1)
            data["actions"].append(action)
        fp.write(json.dumps(data, indent = 4))
        fp.close()
        LOG.debug("test end")
