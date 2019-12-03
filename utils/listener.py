# -*- coding: utf-8 -*-

import logging

from utils.discovery.connection import BaseConnection
from utils.discovery.listener import BaseListener

LOG = logging.getLogger(__name__)


class Connection(BaseConnection):
    pass


class DiscoveryListener(BaseListener):
    pass