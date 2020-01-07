# -*- coding: utf-8 -*-

import os
import signal
import logging

import tornado.ioloop
import tornado.httpserver
import tornado.web

from handlers import info
from handlers import application
from handlers import task
from utils.listener import Connection
from utils.listener import DiscoveryListener
from models.applications import ApplicationsDB
from models.tasks import TasksDB
from utils.scheduler import TaskScheduler
from utils import common
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", info.AboutHandler),
            (r"/cluster/info", info.ClusterInfoHandler),
            (r"/app/create", application.CreateApplicationHandler),
            (r"/app/list", application.ListApplicationHandler),
            (r"/app/delete", application.DeleteApplicationHandler),
            (r"/app/update", application.UpdateApplicationHandler),
            (r"/app/info", application.InfoApplicationHandler),
            (r"/app/download", application.DownloadApplicationHandler),
            (r"/task/create", task.CreateTaskHandler),
            (r"/task/list", task.ListTaskHandler),
            (r"/task/info", task.InfoTaskHandler),
            (r"/task/delete", task.DeleteTaskHandler),
            (r"/task/stop", task.StopTaskHandler),
            (r"/action/update", task.UpdateActionHandler),
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
        http_server = tornado.httpserver.HTTPServer(
            Application(),
            max_buffer_size = CONFIG["max_buffer_size"],
            chunk_size = 10 * 1024 * 1024
        )
        http_server.listen(CONFIG["http_port"], address = CONFIG["http_host"])
        # http_server.bind(CONFIG["http_port"], address = CONFIG["http_host"])
        listener = DiscoveryListener(Connection, TaskScheduler)
        listener.listen(CONFIG["tcp_port"], CONFIG["tcp_host"])
        common.Servers.HTTP_SERVER = http_server
        common.Servers.DB_SERVERS.append(ApplicationsDB)
        common.Servers.DB_SERVERS.append(TasksDB)
        common.Servers.DB_SERVERS.append(TaskScheduler)
        signal.signal(signal.SIGTERM, common.sig_handler)
        signal.signal(signal.SIGINT, common.sig_handler)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        LOG.exception(e)

    LOG.info("service end")
