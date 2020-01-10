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
from litepipeline.models.action import Action

import logger

LOG = logging.getLogger(__name__)

home = str(Path.home())


if __name__ == "__main__":
    workspace, input_data = Action.get_input()

    logs_directory = os.path.join(workspace, "logs")
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

    data = {"messages": []}
    for i in range(10):
        now = datetime.datetime.now()
        message = "%s: hello world, tornado(%03d): %s, numpy: %s" % (now, i, tornado.version, numpy.__version__)
        data["messages"].append(message)
        LOG.debug(message)
        time.sleep(1)

    Action.set_output(data = data)
    LOG.debug("test end")
