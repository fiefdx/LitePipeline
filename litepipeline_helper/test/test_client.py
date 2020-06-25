# -*- coding: utf-8 -*-

import os
import sys
import json
import logging

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

from litepipeline_helper.models.client import LitePipelineClient
from litepipeline.manager import logger

LOG = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.config_logging(file_name = "test_client.log",
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
        c = LitePipelineClient("127.0.0.1", 8000)
        LOG.debug("application list: %s", json.dumps(c.application_list(), indent = 4))
        LOG.debug("application info: %s", json.dumps(c.application_info("296be936-742c-4ae7-ba07-c1bf6a6e9300"), indent = 4))
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
