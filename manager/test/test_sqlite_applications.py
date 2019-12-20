# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

from models.applications import ApplicationsDB 
import logger

LOG = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_sqlite_applications.log",
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
        app_id = ApplicationsDB.add("name 0", "description 0")
        app_id = ApplicationsDB.add("name 1", "description 1")
        app_id = ApplicationsDB.add("name 2", "description 2")
        r = ApplicationsDB.get(app_id)
        LOG.debug("get: %s", r)
        r = ApplicationsDB.list()
        LOG.debug("list: %s", r)
        r = ApplicationsDB.update(app_id, {"name": "name new"})
        LOG.debug("update: %s", r)
        r = ApplicationsDB.list()
        LOG.debug("list: %s", r)
        r = ApplicationsDB.delete(app_id)
        LOG.debug("delete: %s", r)
        r = ApplicationsDB.list()
        LOG.debug("list: %s", r)
        ApplicationsDB.close()
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
