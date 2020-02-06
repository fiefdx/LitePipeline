# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

from utils.persistent_config import PersistentConfig 
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_persistent_config.log",
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
        c = PersistentConfig("./data/configuration.json")
        c.from_dict(CONFIG)
        c.update("http_port", 9999)
        c.db.storage.flush()
        LOG.debug("sleep start")
        time.sleep(60)
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
