#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import stat
import signal
import logging
import argparse
from pathlib import Path

import tornado.ioloop
import tornado.httpserver
import tornado.web

from litepipeline.version import __version__
from litepipeline.manager.handlers import info
from litepipeline.manager.handlers import venv
from litepipeline.manager.handlers import application
from litepipeline.manager.handlers import task
from litepipeline.manager.handlers import workflow
from litepipeline.manager.handlers import work
from litepipeline.manager.handlers import schedule
from litepipeline.manager.handlers import service
from litepipeline.manager.utils.listener import Connection
from litepipeline.manager.utils.listener import DiscoveryListener
from litepipeline.manager.models.venvs import Venvs
from litepipeline.manager.models.venv_history import VenvHistory
from litepipeline.manager.models.applications import Applications
from litepipeline.manager.models.application_history import ApplicationHistory
from litepipeline.manager.models.tasks import Tasks
from litepipeline.manager.models.workflows import Workflows
from litepipeline.manager.models.works import Works
from litepipeline.manager.models.schedules import Schedules
from litepipeline.manager.models.services import Services
from litepipeline.manager.utils.venv_manager import VenvManager
from litepipeline.manager.utils.app_manager import AppManager
from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.utils import common
from litepipeline.manager.utils import stop_service
from litepipeline.manager.utils.litedfs import LDFS, LiteDFS
from litepipeline.manager.config import CONFIG, load_config
from litepipeline import logger

LOG = logging.getLogger(__name__)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", info.AboutHandler),
            (r"/cluster/info", info.ClusterInfoHandler),
            (r"/venv/create", venv.CreateVenvHandler),
            (r"/venv/list", venv.ListVenvHandler),
            (r"/venv/delete", venv.DeleteVenvHandler),
            (r"/venv/update", venv.UpdateVenvHandler),
            (r"/venv/info", venv.InfoVenvHandler),
            (r"/venv/download", venv.DownloadVenvHandler),
            (r"/venv/history/list", venv.VenvHistoryListHandler),
            (r"/venv/history/info", venv.VenvHistoryInfoHandler),
            (r"/venv/history/activate", venv.VenvHistoryActivateHandler),
            (r"/venv/history/delete", venv.VenvHistoryDeleteHandler),
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
    parser.add_argument("-g", "--generate-config", help = "generate configuration file & scripts into given path")
    parser.add_argument("-c", "--config", help = "configuration file path")
    parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)
    args = parser.parse_args()

    if args.generate_config:
        output = args.generate_config
        cwd = os.path.split(os.path.realpath(__file__))[0]
        config_file = os.path.join(cwd, "./configuration.yml.temp")
        copy_files = [
            "install_systemd_service.sh",
            "uninstall_systemd_service.sh",
            "litepipeline-manager.service.temp",
            "manager.sh",
            "README.md",
            "migrate_database.py",
        ]
        if os.path.exists(output) and os.path.isdir(output):
            output = str(Path(output).resolve())
            log_path = os.path.join(output, "logs")
            data_path = os.path.join(output, "data")
            content = ""
            fp = open(config_file, "r")
            content = fp.read()
            fp.close()
            content = content.replace("log_path_string", log_path)
            content = content.replace("data_path_string", data_path)
            fp = open(os.path.join(output, "configuration.yml"), "w")
            fp.write(content)
            fp.close()
            for file_name in copy_files:
                file_path_source = os.path.join(cwd, file_name)
                with open(file_path_source, "r") as fs:
                    file_path_target = os.path.join(output, file_name)
                    with open(file_path_target, "w") as ft:
                        ft.write(fs.read())
                    if file_path_target.endswith(".sh"):
                        os.chmod(
                            file_path_target,
                            stat.S_IRUSR | stat.S_IWUSR | stat.S_IEXEC | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
                        )
        else:
            print("output(%s) not exists!", output)
    elif args.config:
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
                venvs_db = Venvs()
                venv_history_db = VenvHistory()
                tasks_db = Tasks()
                applications_db = Applications()
                application_history_db = ApplicationHistory()
                workflows_db = Workflows()
                works_db = Works()
                schedules_db = Schedules()
                services_db = Services()
                venv_manager = VenvManager()
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
                stop_service.Servers.SERVERS.append(venvs_db)
                stop_service.Servers.SERVERS.append(venv_history_db)
                stop_service.Servers.SERVERS.append(applications_db)
                stop_service.Servers.SERVERS.append(application_history_db)
                stop_service.Servers.SERVERS.append(tasks_db)
                stop_service.Servers.SERVERS.append(workflows_db)
                stop_service.Servers.SERVERS.append(works_db)
                stop_service.Servers.SERVERS.append(schedules_db)
                stop_service.Servers.SERVERS.append(services_db)
                stop_service.Servers.SERVERS.append(venv_manager)
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
