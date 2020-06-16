# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import datetime
from pathlib import Path

import tornado
from litepipeline_helper.models.action import Action
from litedfs_client.client import LiteDFSClient

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

    task_name = input_data["action_info"]["task_name"]
    action_name = input_data["action_info"]["action_name"]
    task_id = input_data["task_id"]

    ldfs_host = input_data["ldfs_host"] if "ldfs_host" in input_data and input_data["ldfs_host"] else None
    ldfs_port = input_data["ldfs_port"] if "ldfs_port" in input_data and input_data["ldfs_port"] else None
    if ldfs_host and ldfs_port:
        ldfs = LiteDFSClient(ldfs_host, ldfs_port)

        first_data_path = input_data["first action"]["ldfs_data_path"]
        second_data_path = input_data["second action"]["ldfs_data_path"]

        first_data = json.loads(ldfs.open_remote_file(first_data_path).read().decode("utf-8"))
        second_data = json.loads(ldfs.open_remote_file(first_data_path).read().decode("utf-8"))

        data = {"messages": []}
        for message in first_data["messages"]:
            data["messages"].append(message)
        for message in second_data["messages"]:
            data["messages"].append(message)
        for i in range(20, 30):
            now = datetime.datetime.now()
            message = "%s: hello world, tornado(%03d): %s" % (now, i, tornado.version)
            data["messages"].append(message)
            LOG.debug(message)
            time.sleep(1)

        data_file_path = os.path.join(workspace, "data.json")
        data_ldfs_path = os.path.join("/litepipeline_test", task_id, "%s.json" % action_name)
        with open(data_file_path, "w") as fp:
            fp.write(json.dumps(data, indent = 4))
        ldfs.create_file(data_file_path, data_ldfs_path, replica = 1)

    Action.set_output(data = {"ldfs_data_path": data_ldfs_path})
    LOG.debug("test end")
