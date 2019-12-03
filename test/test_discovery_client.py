# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

import tornado.ioloop

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

from utils.discovery import DiscoveryRegistrant
import logger

LOG = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_discovery_client.log",
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
        registrant = DiscoveryRegistrant("127.0.0.1", 6001)
        tornado.ioloop.IOLoop.instance().add_callback(registrant.connect)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
