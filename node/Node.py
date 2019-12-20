# -*- coding: utf-8 -*-
import os
import logging

import tornado.ioloop

from utils.registrant import Registrant
from utils.persistent_config import PersistentConfig
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.config_logging(file_name = "node.log",
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
        init_run = True
        if os.path.exists("./configuration.json"):
            init_run = False
        c = PersistentConfig("./configuration.json")
        if init_run:
            c.from_dict(CONFIG)
        registrant = Registrant(CONFIG["manager_host"], CONFIG["manager_port"], c)
        tornado.ioloop.IOLoop.instance().add_callback(registrant.connect)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        LOG.exception(e)

    LOG.info("service end")
