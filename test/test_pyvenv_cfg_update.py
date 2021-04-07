# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.join(os.path.split(cwd)[0], "litepipeline"))

from litepipeline.node.utils.apps_manager import update_venv_cfg
from litepipeline.node import logger
from litepipeline.node.config import CONFIG

LOG = logging.getLogger(__name__)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_pyvenv_cfg_update.log",
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
        update_venv_cfg("./venv")
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
