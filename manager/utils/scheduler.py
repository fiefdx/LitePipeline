# -*- coding: utf-8 -*-

import os
import json
import logging

import tornado.ioloop
import tornado.web
import requests

from models.applications import ApplicationsDB
from models.tasks import TasksDB, Stage, Status
from utils.listener import Connection
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


class Scheduler(object):
    def __init__(self, interval = 1):
        self.interval = interval
        self.ioloop_service()
        self.running_actions = []
        self.pending_actions = []
        self.tasks = {}

    def ioloop_service(self):
        self.periodic_schedule = tornado.ioloop.PeriodicCallback(
            self.schedule_service, 
            self.interval * 1000
        )
        self.periodic_schedule.start()

    def select_node(self):
        result = None
        try:
            for node in Connection.clients:
                if "max_execute_tasks" in node.info and node.info["max_execute_tasks"] > 0:
                    result = node
                    break
        except Exception as e:
            LOG.exception(e)
        return result

    def schedule_service(self):
        LOG.debug("schedule_service")
        try:
            node = self.select_node()
            if node:
                http_host = node.info["http_host"]
                http_port = node.info["http_port"]
                LOG.debug("select node: %s:%s", http_host, http_port)
                task_info = TasksDB.get_first()
                if task_info:
                    task_id = task_info["task_id"]
                    app_id = task_info["application_id"]
                    app_info = ApplicationsDB.get(app_id)
                    if app_info:
                        app_config_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id, "app", "configuration.json")
                        if os.path.exists(app_config_path):
                            fp = open(app_config_path, "r")
                            app_config = json.loads(fp.read())
                            fp.close()
                            for action in app_config["actions"]:
                                action["task_id"] = task_id
                                action["app_id"] = app_id
                                self.pending_actions.append(action)
                            self.tasks[task_id] = {"task_info": task_info, "app_info": app_info}
                            TasksDB.update(task_id, {"stage": Stage.running})
                        else:
                            LOG.error("Scheduler app config file[%s] not exists", app_config_path)
                    elif app_info is None:
                        LOG.error("Scheduler task[%s]'s app_info[%s] not exists", task_id, app_id)
                    else:
                        LOG.error("Scheduler get task[%s]'s app_info[%s] failed", task_id, app_id)
                elif task_info is None:
                    LOG.debug("Scheduler no more task to execute")
                else:
                    LOG.error("Scheduler get task failed")
            else:
                LOG.warning("no selectable node")
            # LOG.debug("task: %s", json.dumps(task_info, indent = 4))
            # LOG.debug("app: %s", json.dumps(app_info, indent = 4))
        except Exception as e:
            LOG.exception(e)

    def close(self):
        try:
            if self.periodic_schedule:
                self.periodic_schedule.stop()
            for task_id in self.tasks:
                TasksDB.update(task_id, {"stage": Stage.pending})
            LOG.debug("Scheduler close")
        except Exception as e:
            LOG.exception(e)


TaskScheduler = Scheduler()
