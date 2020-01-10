# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import datetime
from pathlib import Path

import tornado

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

        logger.config_logging(file_name = "second.log",
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
        data = {"messages": input_data["messages"]}
        fp.write(json.dumps(data, indent = 4))
        fp.close()
        LOG.debug("test end")
