# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

from utils.discovery import crc32sum
import logger

LOG = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_discovery.log",
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
        s = crc32sum("this is a test")
        LOG.debug("s: %s", s)
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
