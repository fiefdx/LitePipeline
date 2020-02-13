# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

from litepipeline.node.utils.persistent_config import PersistentConfig 
from litepipeline.node import logger

LOG = logging.getLogger(__name__)

cwd = os.path.split(os.path.realpath(__file__))[0]

CONFIG = {
    "http_host": "localhost",
    "http_port": 8000,
}


if __name__ == "__main__":
    logger.config_logging(file_name = "test_persistent_config.log",
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
        c = PersistentConfig("./configuration.json")
        c.from_dict(CONFIG)
        c.update("http_port", 9999)
        # c.db.storage.flush()
        LOG.debug("sleep start")
        time.sleep(60)
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
