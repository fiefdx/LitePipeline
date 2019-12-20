# -*- coding: utf-8 -*-

import logging

from tornado_discovery.connection import BaseConnection
from tornado_discovery.listener import BaseListener

LOG = logging.getLogger(__name__)


class Connection(BaseConnection):
    pass


class DiscoveryListener(BaseListener):
    pass