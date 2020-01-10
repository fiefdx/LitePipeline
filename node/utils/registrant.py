# -*- coding: utf-8 -*-

import os
import sys
import logging

from tornado_discovery.registrant import BaseRegistrant

from utils.persistent_config import PersistentConfig
from config import CONFIG

LOG = logging.getLogger(__name__)

init_run = True
if os.path.exists("./configuration.json"):
    init_run = False
C = PersistentConfig("./configuration.json")
if init_run:
    C.from_dict(CONFIG)
C.set("python3", sys.version)


class Registrant(BaseRegistrant):
    pass


NodeRegistrant = Registrant(
    CONFIG["manager_tcp_host"],
    CONFIG["manager_tcp_port"],
    C,
    retry_interval = CONFIG["retry_interval"]
)
