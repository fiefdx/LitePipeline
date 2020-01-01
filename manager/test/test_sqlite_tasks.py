# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

from models.tasks import TasksDB
import logger

LOG = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_tasks.log",
                          log_level = "DEBUG",
                          dir_name = "logs",
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)

    LOG.debug("test start")

    try:
        task_id = TasksDB.add("name 0", "app 0", {"0": "source 0"})
        task_id = TasksDB.add("name 1", "app 1", {"1": "source 1"})
        task_id = TasksDB.add("name 2", "app 2", {"2": "source 2"})
        r = TasksDB.get(task_id)
        LOG.debug("get: %s", r)
        r = TasksDB.list()
        LOG.debug("list: %s", r)
        r = TasksDB.update(task_id, {"task_name": "name new"})
        LOG.debug("update: %s", r)
        r = TasksDB.list()
        LOG.debug("list: %s", r)
        r = TasksDB.delete(task_id)
        LOG.debug("delete: %s", r)
        r = TasksDB.list()
        LOG.debug("list: %s", r)
        r = TasksDB.get_first()
        LOG.debug("get_first: %s", r)
        TasksDB.close()
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
