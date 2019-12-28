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
from utils.common import Errors
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
        self.periodic_execute = tornado.ioloop.PeriodicCallback(
            self.execute_service, 
            self.interval * 1000
        )
        self.periodic_execute.start()

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

    def select_executable_action(self):
        result = None
        try:
            for action in self.pending_actions:
                if set(action["conditions"]).issubset(set(self.tasks[action["task_id"]]["finished"].keys())):
                    result = action
                    break
        except Exception as e:
            LOG.exception(e)
        return result

    def execute_service(self):
        LOG.debug("execute_service")
        try:
            node = self.select_node() 
            if node:
                http_host = node.info["http_host"]
                http_port = node.info["http_port"]
                LOG.debug("select node: %s:%s", http_host, http_port)
                action = self.select_executable_action()
                LOG.info("seleted action: %s", action)
                if action:
                    url = "http://%s:%s/app/run" % (http_host, http_port)
                    r = requests.post(url, json = action)
                    r_json = r.json()
                    if r.status_code == 200 and "result" in r_json and r_json["result"] == Errors.OK:
                        LOG.warning(r.json())
                        self.pending_actions.remove(action)
                        self.running_actions.append(action)
                        LOG.debug("migrate action[%s][%s] to running", action["task_id"], action["name"])
                    else:
                        LOG.error("request node[%s] for action[%s][%s] failed", url, action["task_id"], action["name"])
                else:
                    LOG.debug("no more executable action")
            else:
                LOG.warning("no selectable node")
        except Exception as e:
            LOG.exception(e)

    def schedule_service(self):
        LOG.debug("schedule_service")
        try:
            node = self.select_node() # should be checking calculate resource
            if node:
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
                                action["app_sha1"] = app_info["sha1"]
                                if len(action["conditions"]) == 0:
                                    action["source"] = task_info["source"]
                                self.pending_actions.append(action)
                            self.tasks[task_id] = {"task_info": task_info, "app_info": app_info, "finished": {}}
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
            if self.periodic_execute:
                self.periodic_execute.stop()
            for task_id in self.tasks:
                TasksDB.update(task_id, {"stage": Stage.pending})
            LOG.debug("Scheduler close")
        except Exception as e:
            LOG.exception(e)


TaskScheduler = Scheduler()
