# -*- coding: utf-8 -*-

import os
import json
import logging
import time
import datetime
from copy import deepcopy

from tornado import ioloop
from tornado import gen

from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.config import CONFIG
from litepipeline.manager import logger

LOG = logging.getLogger(__name__)


class Servers(object):
    HTTP_SERVER = None
    SERVERS = []
    TORNADO_INSTANCE = None


class StopService(object):
    _instance = None
    name = "stop_service"

    def __new__(cls, interval = 1):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.interval = interval
            cls._instance.services = [
                Scheduler.instance()
            ]
            cls._instance.running = False
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def stop(self):
        if not self.running:
            self.running = True
            self.periodic_crontab = ioloop.PeriodicCallback(
                self.stop_service,
                5 * 1000 # 30 seconds
            )
            self.periodic_crontab.start()
        else:
            LOG.warning("stop service already running")

    @gen.coroutine
    def stop_service(self):
        LOG.debug("stop_service")
        try:
            ready = 0
            for service in self.services:
                if service.name == "scheduler":
                    if not service.stop:
                        service.stop = True
                    else:
                        if len(service.tasks) > 0:
                            LOG.warning("some task still running: %s", len(service.tasks))
                        else:
                            LOG.info("all task stopped")
                            service.close()
                            ready += 1
                            break
            if len(self.services) == ready:
                for s in Servers.SERVERS:
                    s.close()
                    if hasattr(s, "name"):
                        LOG.info("Stop %s server!", s.name)
                    else:
                        LOG.info("Stop nameless server!")
                ioloop.IOLoop.current().add_callback_from_signal(self.shutdown)
        except Exception as e:
            LOG.exception(e)

    async def shutdown(self):
        LOG.info("Stopping Service(%s:%s)", CONFIG["http_host"], CONFIG["http_port"])
        if Servers.HTTP_SERVER:
            Servers.HTTP_SERVER.stop()
            LOG.info("Stop http server!")
        await gen.sleep(1)
        LOG.info("Will shutdown ...")
        ioloop.IOLoop.current().stop()


async def shutdown():
    s = StopService()
    s.stop()


def sig_handler(sig, frame):
    LOG.warning("sig_handler Caught signal: %s", sig)
    ioloop.IOLoop.current().add_callback_from_signal(shutdown)
