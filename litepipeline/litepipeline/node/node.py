#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import signal
import logging
import argparse
import platform

import tornado.ioloop
import tornado.httpserver
import tornado.web

from litepipeline.version import __version__
from litepipeline.node.handlers import info
from litepipeline.node.handlers import action
from litepipeline.node.handlers import task
from litepipeline.node.utils.registrant import Registrant
from litepipeline.node.utils.executor import Executor
from litepipeline.node.utils import common
from litepipeline.node.utils.apps_manager import ManagerClient as AppsManagerClient
from litepipeline.node.utils.workspace_manager import ManagerClient as WorkspaceManagerClient
from litepipeline.node.utils.persistent_config import PersistentConfig
from litepipeline.node.config import CONFIG, load_config
from litepipeline.node import logger

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", info.AboutHandler),
            (r"/action/run", action.RunActionHandler),
            (r"/action/stop", action.StopActionHandler),
            (r"/action/cancel", action.CancelActionHandler),
            (r"/status/full", action.FullStatusHandler),
            (r"/workspace/pack", action.PackWorkspaceHandler),
            (r"/workspace/download", action.DownloadWorkspaceHandler),
            (r"/workspace/delete", task.DeleteTaskWorkspaceHandler),
        ]
        settings = dict(debug = False)
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    parser = argparse.ArgumentParser(prog = 'litenode')
    parser.add_argument("-c", "--config", required = True, help = "configuration file path")
    parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)
    args = parser.parse_args()

    if args.config:
        success = load_config(args.config)
        if success:
            common.init_storage()
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
                config_file_path = os.path.join(CONFIG["data_path"], "configuration.json")
                if os.path.exists(config_file_path):
                    init_run = False
                C = PersistentConfig(config_file_path)
                if init_run:
                    C.from_dict(CONFIG)
                C.set("python3", sys.version)
                C.set("version", __version__)
                C.set("platform", platform.machine())

                node_registrant = Registrant(
                    C["manager_tcp_host"],
                    C["manager_tcp_port"],
                    C,
                    retry_interval = C["retry_interval"]
                )
                action_executor = Executor(C)

                http_server = tornado.httpserver.HTTPServer(Application())
                http_server.listen(C["http_port"], address = C["http_host"])
                # http_server.bind(C["http_port"], address = C["http_host"])
                common.Servers.HTTP_SERVER = http_server
                common.Servers.DB_SERVERS.append(action_executor)
                common.Servers.DB_SERVERS.append(AppsManagerClient())
                common.Servers.DB_SERVERS.append(WorkspaceManagerClient())
                tornado.ioloop.IOLoop.instance().add_callback(node_registrant.connect)
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
