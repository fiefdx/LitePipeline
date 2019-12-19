# -*- coding: utf-8 -*-

import os
import signal
import logging

import tornado.ioloop
import tornado.httpserver
import tornado.web

from handlers.info import AboutHandler
from handlers.application import DeployHandler
from utils.listener import Connection
from utils.listener import DiscoveryListener
from models.applications import ApplicationsDB
from models.tasks_status import TasksStatusDB
from models.tasks import TasksDB
from utils import common
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", AboutHandler),
            (r"/deploy", DeployHandler),
        ]
        settings = dict(debug = False)
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    logger.config_logging(file_name = "manager.log",
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
        listener = DiscoveryListener(Connection)
        listener.listen(CONFIG["tcp_port"], CONFIG["tcp_host"])
        common.Servers.HTTP_SERVER = http_server
        common.Servers.DB_SERVERS.append(ApplicationsDB)
        common.Servers.DB_SERVERS.append(TasksStatusDB)
        common.Servers.DB_SERVERS.append(TasksDB)
        signal.signal(signal.SIGTERM, common.sig_handler)
        signal.signal(signal.SIGINT, common.sig_handler)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        LOG.exception(e)

    LOG.info("service end")
