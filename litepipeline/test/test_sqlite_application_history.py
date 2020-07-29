# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

from litepipeline.manager.models.application_history import ApplicationHistory 
from litepipeline.manager import logger
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_sqlite_application_history.log",
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
        CONFIG["data_path"] = cwd

        db = ApplicationHistory()

        LOG.debug("add: %s", db.add("id_1", "sha1_1", "description_1"))
        LOG.debug("add: %s", db.add("id_1", "sha1_2", "description_2"))
        LOG.debug("add: %s", db.add("id_1", "sha1_3", "description_3"))
        LOG.debug("add: %s", db.add("id_2", "sha1_4", "description_4"))
        LOG.debug("add: %s", db.add("id_2", "sha1_5", "description_5"))
        LOG.debug("add: %s", db.add("id_3", "sha1_6", "description_6"))

        LOG.debug("list: %s", json.dumps(db.list(), indent = 4))
        LOG.debug("list id_1: %s", json.dumps(db.list(filters = {"id": "id_1"}), indent = 4))
        LOG.debug("latest id_1: %s", json.dumps(db.get_latest("id_1"), indent = 4))

        LOG.debug("delete id_1: %s", db.delete_by_app_id("id_1"))
        LOG.debug("list id_1: %s", json.dumps(db.list(filters = {"id": "id_1"}), indent = 4))

        LOG.debug("delete 6: %s", db.delete(6))
        LOG.debug("list: %s", json.dumps(db.list(), indent = 4))

        db.close()
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
