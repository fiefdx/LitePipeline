# -*- coding: utf-8 -*-

import os
import sys
import logging

from tornado_discovery.registrant import BaseRegistrant

from litepipeline.node.utils.persistent_config import PersistentConfig
from litepipeline.version import __version__
from litepipeline.node.utils import common
from litepipeline.node.config import CONFIG

LOG = logging.getLogger(__name__)

common.init_storage()
init_run = True
config_file_path = os.path.join(CONFIG["data_path"], "configuration.json")
if os.path.exists(config_file_path):
    init_run = False
C = PersistentConfig(config_file_path)
if init_run:
    C.from_dict(CONFIG)
C.set("python3", sys.version)
C.set("version", __version__)


class Registrant(BaseRegistrant):
    pass


NodeRegistrant = Registrant(
    CONFIG["manager_tcp_host"],
    CONFIG["manager_tcp_port"],
    C,
    retry_interval = CONFIG["retry_interval"]
)
