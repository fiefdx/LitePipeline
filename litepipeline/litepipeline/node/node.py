#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal
import logging

import tornado.ioloop
import tornado.httpserver
import tornado.web

from litepipeline.node.handlers import info
from litepipeline.node.handlers import action
from litepipeline.node.utils.registrant import NodeRegistrant
from litepipeline.node.utils.executor import ActionExecutor
from litepipeline.node.utils import common
from litepipeline.node.utils.apps_manager import ManagerClient
from litepipeline.node.config import CONFIG
from litepipeline.node import logger

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", info.AboutHandler),
            (r"/action/run", action.RunActionHandler),
            (r"/action/stop", action.StopActionHandler),
            (r"/status/full", action.FullStatusHandler),
        ]
        settings = dict(debug = False)
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    logger.config_logging(file_name = "node.log",
                          log_level = CONFIG["log_level"],
                          dir_name = CONFIG["log_path"],
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)
    LOG.info("service start")

    try:
        http_server = tornado.httpserver.HTTPServer(Application())
        http_server.listen(CONFIG["http_port"], address = CONFIG["http_host"])
        # http_server.bind(CONFIG["http_port"], address = CONFIG["http_host"])
        common.Servers.HTTP_SERVER = http_server
        common.Servers.DB_SERVERS.append(ActionExecutor)
        common.Servers.DB_SERVERS.append(ManagerClient())
        tornado.ioloop.IOLoop.instance().add_callback(NodeRegistrant.connect)
        signal.signal(signal.SIGTERM, common.sig_handler)
        signal.signal(signal.SIGINT, common.sig_handler)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        LOG.exception(e)

    LOG.info("service end")


if __name__ == "__main__":
    main()
