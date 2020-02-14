#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal
import logging
import argparse

import tornado.ioloop
import tornado.httpserver
import tornado.web

from litepipeline.version import __version__
from litepipeline.manager.handlers import info
from litepipeline.manager.handlers import application
from litepipeline.manager.handlers import task
from litepipeline.manager.utils.listener import Connection
from litepipeline.manager.utils.listener import DiscoveryListener
from litepipeline.manager.models.applications import Applications
from litepipeline.manager.models.tasks import Tasks
from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.utils import common
from litepipeline.manager.config import CONFIG, load_config
from litepipeline.manager import logger

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


def main():
    parser = argparse.ArgumentParser(prog = 'litemanager')
    parser.add_argument("-c", "--config", required = True, help = "configuration file path")
    parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)
    args = parser.parse_args()

    if args.config:
        success = load_config(args.config)
        if success:
            common.init_storage()
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
                tasks_db = Tasks()
                applications_db = Applications()
                task_scheduler = Scheduler(CONFIG["scheduler_interval"])
                http_server = tornado.httpserver.HTTPServer(
                    Application(),
                    max_buffer_size = CONFIG["max_buffer_size"],
                    chunk_size = 10 * 1024 * 1024
                )
                http_server.listen(CONFIG["http_port"], address = CONFIG["http_host"])
                # http_server.bind(CONFIG["http_port"], address = CONFIG["http_host"])
                listener = DiscoveryListener(Connection, task_scheduler)
                listener.listen(CONFIG["tcp_port"], CONFIG["tcp_host"])
                common.Servers.HTTP_SERVER = http_server
                common.Servers.DB_SERVERS.append(applications_db)
                common.Servers.DB_SERVERS.append(tasks_db)
                common.Servers.DB_SERVERS.append(task_scheduler)
                signal.signal(signal.SIGTERM, common.sig_handler)
                signal.signal(signal.SIGINT, common.sig_handler)
                tornado.ioloop.IOLoop.instance().start()
            except Exception as e:
                LOG.exception(e)

            LOG.info("service end")
        else:
            print("failed to load configuration: %s" % args.config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
