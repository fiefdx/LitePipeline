# -*- coding: utf-8 -*-

import os
import json
import logging
import datetime

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.ioloop
import tornado.web
from tornado import gen

from models.applications import ApplicationsDB
from models.tasks import TasksDB
from utils.listener import Connection
from utils.common import Errors, Stage, Status
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
        self.async_client = AsyncHTTPClient()

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

    @gen.coroutine
    def select_node(self):
        result = None
        try:
            for node in Connection.clients:
                http_host = node.info["http_host"]
                http_port = node.info["http_port"]
                LOG.debug("checking node full, %s:%s", http_host, http_port)
                url = "http://%s:%s/status/full" % (http_host, http_port)
                request = HTTPRequest(url = url, method = "GET")
                r = yield self.async_client.fetch(request)
                if r.code == 200:
                    data = json.loads(r.body.decode("utf-8"))
                    if data["result"] == Errors.OK:
                        if not data["full"]:
                            result = node
                            break
                else:
                    LOG.error("checking node full failed, %s", url)
        except Exception as e:
            LOG.exception(e)
        raise gen.Return(result)

    def select_executable_action(self):
        result = None
        try:
            for action in self.pending_actions:
                if set(action["conditions"]).issubset(set(self.tasks[action["task_id"]]["finished"].keys())):
                    for condition_name in action["conditions"]:
                        if "source" not in action:
                            action["source"] = {condition_name: self.tasks[action["task_id"]]["finished"][condition_name]["result"]}
                        else:
                            action["source"][condition_name] = self.tasks[action["task_id"]]["finished"][condition_name]["result"]
                    result = action
                    break
        except Exception as e:
            LOG.exception(e)
        return result

    def schedule_finish_action(self):
        try:
            for action in self.running_actions:
                pass
        except Exception as e:
            LOG.exception(e)

    def update_finish_action(self, action_result):
        try:
            action_finish = None
            task_id = action_result["task_id"]
            action_name = action_result["name"]
            now = datetime.datetime.now()
            for action in self.running_actions:
                if action["task_id"] == task_id and action["name"] == action_name:
                    action_finish = action
                    break
            if action_finish:
                if action_result["status"] == Status.success:
                    self.tasks[task_id]["finished"][action_finish["name"]] = action_result
                    self.running_actions.remove(action_finish)
                    finish_condition = self.tasks[task_id]["condition"]
                    current_condition = self.tasks[task_id]["finished"].keys()
                    if len(current_condition) == len(finish_condition):
                        TasksDB.update(task_id, {"stage": Stage.finished, "status": Status.success, "end_at": now, "result": self.tasks[task_id]["finished"]})
                        del self.tasks[task_id]
                    else:
                        TasksDB.update(task_id, {"result": self.tasks[task_id]["finished"]})
                else:
                    pending_actions_tmp = []
                    running_actions_tmp = []
                    for action in self.pending_actions:
                        if action["task_id"] != task_id:
                            pending_actions_tmp.append(action)
                    self.pending_actions = pending_actions_tmp
                    for action in self.running_actions:
                        if action["task_id"] != task_id:
                            running_actions_tmp.append(action)
                    self.running_actions = running_actions_tmp
                    TasksDB.update(task_id, {"stage": Stage.finished, "status": Status.failed, "end_at": now, "result": self.tasks[task_id]["finished"]}) # need task result display
                    del self.tasks[task_id]
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def execute_service(self):
        LOG.debug("execute_service")
        try:
            node = yield self.select_node() 
            if node:
                http_host = node.info["http_host"]
                http_port = node.info["http_port"]
                LOG.debug("select node: %s:%s", http_host, http_port)
                action = self.select_executable_action()
                LOG.info("seleted action: %s", action)
                if action:
                    url = "http://%s:%s/action/run" % (http_host, http_port)
                    request = HTTPRequest(url = url, method = "POST", body = json.dumps(action))
                    r = yield self.async_client.fetch(request)
                    if r.code == 200 and json.loads(r.body.decode("utf-8"))["result"] == Errors.OK:
                        self.pending_actions.remove(action)
                        action["node"] = "%s:%s" % (http_host, http_port)
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

    @gen.coroutine
    def schedule_service(self):
        LOG.debug("schedule_service")
        try:
            node = yield self.select_node() # should be checking calculate resource
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
                            finish_condition = []
                            for action in app_config["actions"]:
                                action["task_id"] = task_id
                                action["app_id"] = app_id
                                action["app_sha1"] = app_info["sha1"]
                                if len(action["conditions"]) == 0:
                                    action["source"] = task_info["source"]
                                finish_condition.append(action["name"])
                                self.pending_actions.append(action)
                            self.tasks[task_id] = {"task_info": task_info, "condition": finish_condition, "app_info": app_info, "finished": {}}
                            TasksDB.update(task_id, {"stage": Stage.running, "start_at": datetime.datetime.now()})
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
