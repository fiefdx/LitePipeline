# -*- coding: utf-8 -*-

import os
import logging

import tornado.ioloop

from utils.listener import Connection
from utils.listener import DiscoveryListener
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.config_logging(file_name = "manager.log",
                          log_level = CONFIG["log_level"],
                          dir_name = CONFIG["log_path"],
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)

    LOG.info("service start")
    
    try:
        listener = DiscoveryListener(Connection)
        listener.listen(CONFIG["tcp_port"], CONFIG["tcp_host"])
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        LOG.exception(e)

    LOG.info("service end")
