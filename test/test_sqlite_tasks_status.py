# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

from litepipeline.manager.models.tasks_status import TasksStatusDB 
from litepipeline.manager import logger

LOG = logging.getLogger(__name__)

cwd = os.path.split(os.path.realpath(__file__))[0]



if __name__ == "__main__":
    logger.config_logging(file_name = "test_tasks_status.log",
                          log_level = "DEBUG",
                          dir_name = os.path.join(cwd, "logs"),
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)

    LOG.debug("test start")
    
    try:
        task_id = TasksStatusDB.add("name 0", "app 0", "app name 0", "pending")
        task_id = TasksStatusDB.add("name 1", "app 1", "app name 1", "pending")
        task_id = TasksStatusDB.add("name 2", "app 2", "app name 2", "pending")
        r = TasksStatusDB.get(task_id)
        LOG.debug("get: %s", r)
        r = TasksStatusDB.list()
        LOG.debug("list: %s", r)
        r = TasksStatusDB.update(task_id, {"task_name": "name new"})
        LOG.debug("update: %s", r)
        r = TasksStatusDB.list()
        LOG.debug("list: %s", r)
        r = TasksStatusDB.delete(task_id)
        LOG.debug("delete: %s", r)
        r = TasksStatusDB.list()
        LOG.debug("list: %s", r)
        TasksStatusDB.close()
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
