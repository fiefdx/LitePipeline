# -*- coding: utf-8 -*-
import os
import signal
import logging

import tornado.ioloop
import tornado.httpserver
import tornado.web

from handlers.info import AboutHandler
from handlers.action import RunActionHandler, FullStatusHandler
from utils.registrant import Registrant
from utils.persistent_config import PersistentConfig
from utils.executor import ActionExecutor
from utils import common
from utils.apps_manager import AppsManager
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", AboutHandler),
            (r"/action/run", RunActionHandler),
            (r"/status/full", FullStatusHandler),
        ]
        settings = dict(debug = False)
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
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
        init_run = True
        if os.path.exists("./configuration.json"):
            init_run = False
        c = PersistentConfig("./configuration.json")
        if init_run:
            c.from_dict(CONFIG)
        http_server = tornado.httpserver.HTTPServer(Application())
        http_server.listen(CONFIG["http_port"], address = CONFIG["http_host"])
        # http_server.bind(CONFIG["http_port"], address = CONFIG["http_host"])
        common.Servers.HTTP_SERVER = http_server
        registrant = Registrant(
            CONFIG["manager_tcp_host"],
            CONFIG["manager_tcp_port"],
            c,
            retry_interval = CONFIG["retry_interval"]
        )
        common.Servers.DB_SERVERS.append(ActionExecutor)
        common.Servers.DB_SERVERS.append(AppsManager)
        tornado.ioloop.IOLoop.instance().add_callback(registrant.connect)
        signal.signal(signal.SIGTERM, common.sig_handler)
        signal.signal(signal.SIGINT, common.sig_handler)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        LOG.exception(e)

    LOG.info("service end")
