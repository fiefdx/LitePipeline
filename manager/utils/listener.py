# -*- coding: utf-8 -*-

import logging

import tornado.tcpserver
from tornado.ioloop import IOLoop
from tornado_discovery.connection import BaseConnection
from tornado_discovery.listener import BaseListener

LOG = logging.getLogger(__name__)


class Connection(BaseConnection):
    def __init__(self, stream, address, scheduler):
        super(Connection, self).__init__(stream, address)
        self.scheduler = scheduler

    def _remove_connection(self):
        if self in BaseConnection.clients:
            BaseConnection.clients.remove(self)
        if "node_id" in self.info:
            self.scheduler.repending_running_actions(self.info["node_id"])
        self._stream.close()
        LOG.warning("Client(%s) node_id: %s heartbeat_timeout", self._address, self.info["node_id"])

    def _refuse_connect(self):
        if self._heartbeat_timeout:
            IOLoop.instance().remove_timeout(self._heartbeat_timeout)
        if self in BaseConnection.clients:
            BaseConnection.clients.remove(self)
        if "node_id" in self.info:
            self.scheduler.repending_running_actions(self.info["node_id"])
        self._stream.close()
        LOG.warning("Refuse(%s) node_id: %s connect", self._address, self.info["node_id"])

    def _on_close(self):
        if self._heartbeat_timeout:
            IOLoop.instance().remove_timeout(self._heartbeat_timeout)
        if self in BaseConnection.clients:
            BaseConnection.clients.remove(self)
        if "node_id" in self.info:
            self.scheduler.repending_running_actions(self.info["node_id"])
        self._stream.close()
        LOG.info("Client(%s) closed", self._address)


class DiscoveryListener(BaseListener):
    def __init__(self, connection_cls, scheduler, ssl_options = None, **kwargs):
        LOG.info("DiscoveryListener start")
        self.connection_cls = connection_cls
        self.scheduler = scheduler
        tornado.tcpserver.TCPServer.__init__(self, ssl_options = ssl_options, **kwargs)

    def handle_stream(self, stream, address):
        LOG.debug("Incoming connection from %r", address)
        self.connection_cls(stream, address, self.scheduler)
