# -*- coding: utf-8 -*-

import os
import time
import json
import hashlib
import logging

from tornado import ioloop
from tornado import gen

from litedfs_client.client import LiteDFSClient

from litepipeline.manager.config import CONFIG

LOG = logging.getLogger(__name__)
LDFS = None


class LiteDFS(object):
    def __init__(self, host, port):
        self.client = LiteDFSClient(host, port)
