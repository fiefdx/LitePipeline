# -*- coding: utf-8 -*-

import logging

from tornado.tcpclient import TCPClient
from tornado_discovery.registrant import BaseRegistrant

from litepipeline.node.config import CONFIG

LOG = logging.getLogger(__name__)


class Registrant(BaseRegistrant):
    _instance = None

    def __new__(cls, host, port, config, retry_interval = 10, reconnect = True):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.host = host
            cls._instance.port = port
            cls._instance.config = config
            cls._instance.retry_interval = retry_interval
            cls._instance.heartbeat_interval = cls._instance.config.get("heartbeat_interval")
            cls._instance.heartbeat_timeout = cls._instance.config.get("heartbeat_timeout")
            cls._instance.reconnect = reconnect
            cls._instance.tcpclient = TCPClient()
            cls._instance.periodic_heartbeat = None
            cls._instance._stream = None
        return cls._instance

    def __init__(self, host, port, config, retry_interval = 10, reconnect = True):
        pass

    @classmethod
    def instance(cls):
        return cls._instance
