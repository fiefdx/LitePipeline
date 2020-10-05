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
from litepipeline.manager.handlers import workflow
from litepipeline.manager.handlers import work
from litepipeline.manager.handlers import schedule
from litepipeline.manager.handlers import service
from litepipeline.manager.utils.listener import Connection
from litepipeline.manager.utils.listener import DiscoveryListener
from litepipeline.manager.models.applications import Applications
from litepipeline.manager.models.application_history import ApplicationHistory
from litepipeline.manager.models.tasks import Tasks
from litepipeline.manager.models.workflows import Workflows
from litepipeline.manager.models.works import Works
from litepipeline.manager.models.schedules import Schedules
from litepipeline.manager.models.services import Services
from litepipeline.manager.utils.app_manager import AppManager
from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.utils import common
from litepipeline.manager.utils import stop_service
from litepipeline.manager.utils.litedfs import LDFS, LiteDFS
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
            (r"/app/history/list", application.ApplicationHistoryListHandler),
            (r"/app/history/info", application.ApplicationHistoryInfoHandler),
            (r"/app/history/activate", application.ApplicationHistoryActivateHandler),
            (r"/app/history/delete", application.ApplicationHistoryDeleteHandler),
            (r"/task/create", task.CreateTaskHandler),
            (r"/task/list", task.ListTaskHandler),
            (r"/task/info", task.InfoTaskHandler),
            (r"/task/delete", task.DeleteTaskHandler),
            (r"/task/rerun", task.RunTaskHandler),
            (r"/task/recover", task.RecoverTaskHandler),
            (r"/task/stop", task.StopTaskHandler),
            (r"/action/update", task.UpdateActionHandler),
            (r"/workspace/delete", task.DeleteTaskWorkspaceHandler),
            (r"/workspace/pack", task.PackTaskWorkspaceHandler),
            (r"/workspace/download", task.DownloadTaskWorkspaceHandler),
            (r"/workflow/create", workflow.CreateWorkflowHandler),
            (r"/workflow/list", workflow.ListWorkflowHandler),
            (r"/workflow/delete", workflow.DeleteWorkflowHandler),
            (r"/workflow/update", workflow.UpdateWorkflowHandler),
            (r"/workflow/info", workflow.InfoWorkflowHandler),
            (r"/work/create", work.CreateWorkHandler),
            (r"/work/list", work.ListWorkHandler),
            (r"/work/info", work.InfoWorkHandler),
            (r"/work/delete", work.DeleteWorkHandler),
            (r"/work/rerun", work.RunWorkHandler),
            (r"/work/recover", work.RecoverWorkHandler),
            (r"/work/stop", work.StopWorkHandler),
            (r"/schedule/create", schedule.CreateScheduleHandler),
            (r"/schedule/update", schedule.UpdateScheduleHandler),
            (r"/schedule/list", schedule.ListScheduleHandler),
            (r"/schedule/delete", schedule.DeleteScheduleHandler),
            (r"/schedule/info", schedule.InfoScheduleHandler),
            (r"/service/create", service.CreateServiceHandler),
            (r"/service/update", service.UpdateServiceHandler),
            (r"/service/list", service.ListServiceHandler),
            (r"/service/delete", service.DeleteServiceHandler),
            (r"/service/info", service.InfoServiceHandler),
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
                if CONFIG["ldfs_http_host"] and CONFIG["ldfs_http_port"]:
                    LDFS = LiteDFS(CONFIG["ldfs_http_host"], CONFIG["ldfs_http_port"])
                tasks_db = Tasks()
                applications_db = Applications()
                application_history_db = ApplicationHistory()
                workflows_db = Workflows()
                works_db = Works()
                schedules_db = Schedules()
                services_db = Services()
                app_manager = AppManager()
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
                stop_service.Servers.HTTP_SERVER = http_server
                stop_service.Servers.SERVERS.append(task_scheduler)
                stop_service.Servers.SERVERS.append(applications_db)
                stop_service.Servers.SERVERS.append(application_history_db)
                stop_service.Servers.SERVERS.append(tasks_db)
                stop_service.Servers.SERVERS.append(workflows_db)
                stop_service.Servers.SERVERS.append(works_db)
                stop_service.Servers.SERVERS.append(schedules_db)
                stop_service.Servers.SERVERS.append(services_db)
                stop_service.Servers.SERVERS.append(app_manager)
                signal.signal(signal.SIGTERM, stop_service.sig_handler)
                signal.signal(signal.SIGINT, stop_service.sig_handler)
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
