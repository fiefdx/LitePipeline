# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import datetime
from pathlib import Path

import tornado
from litepipeline.client.models.action import Action

import logger

LOG = logging.getLogger(__name__)

home = str(Path.home())


if __name__ == "__main__":
    workspace, input_data = Action.get_input()

    logs_directory = os.path.join(workspace, "logs")
    logger.config_logging(file_name = "third.log",
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
    for key in input_data.keys():
        if "second" in key:
            for message in input_data[key]["messages"]:
                data["messages"].append(message)
    for i in range(20, 30):
        now = datetime.datetime.now()
        message = "%s: hello world, tornado(%03d): %s" % (now, i, tornado.version)
        data["messages"].append(message)
        LOG.debug(message)
        time.sleep(1)

    Action.set_output(data = data)
    LOG.debug("test end")
