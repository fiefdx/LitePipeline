# -*- coding: utf-8 -*-

import os
import json
import logging
import datetime

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.ioloop
import tornado.web
from tornado import gen

from litepipeline.manager.models.applications import Applications
from litepipeline.manager.models.tasks import Tasks
from litepipeline.manager.utils.listener import Connection
from litepipeline.manager.utils.common import Errors, Stage, Status, OperationError
from litepipeline.manager.config import CONFIG
from litepipeline.manager import logger

LOG = logging.getLogger(__name__)


class Scheduler(object):
    _instance = None

    def __new__(cls, interval = 1):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.interval = interval
            cls._instance.ioloop_service()
            cls._instance.running_actions = []
            cls._instance.pending_actions = []
            cls._instance.tasks = {}
            cls._instance.async_client = AsyncHTTPClient()
            cls._instance.current_select_index = 0
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

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
            LOG.debug("clients_dict: %s, total_action_slots: %s", Connection.clients_dict, Connection.total_action_slots)
            for node in Connection.clients:
                if "http_host" in node.info and "http_port" in node.info:
                    http_host = node.info["http_host"]
                    http_port = node.info["http_port"]
                    LOG.debug("checking node full, %s:%s", http_host, http_port)
                    url = "http://%s:%s/status/full" % (http_host, http_port)
                    request = HTTPRequest(url = url, method = "GET")
                    try:
                        r = yield self.async_client.fetch(request)
                        if r.code == 200:
                            data = json.loads(r.body.decode("utf-8"))
                            if data["result"] == Errors.OK:
                                if not data["full"]:
                                    result = node
                                    break
                        else:
                            LOG.error("checking node full failed, %s", url)
                    except ConnectionRefusedError as e:
                        LOG.warning("Scheduler.select_node: GET %s, %s", url, e)
        except Exception as e:
            LOG.exception(e)
        raise gen.Return(result)

    @gen.coroutine
    def select_node_balanced(self):
        result = None
        try:
            LOG.debug("clients_dict: %s, total_action_slots: %s", Connection.clients_dict, Connection.total_action_slots)
            node_ids_tmp = list(Connection.clients_dict.keys())
            node_ids_tmp.sort()
            node_ids = []
            if self.current_select_index >= len(node_ids_tmp):
                self.current_select_index = 0
            if self.current_select_index < 0:
                self.current_select_index = 0
            node_ids.extend(node_ids_tmp[self.current_select_index:])
            node_ids.extend(node_ids_tmp[:self.current_select_index])
            LOG.info("node_ids: %s, %s", node_ids, self.current_select_index)
            for i, node_id in enumerate(node_ids):
                node = Connection.clients_dict[node_id]
                if "http_host" in node.info and "http_port" in node.info:
                    http_host = node.info["http_host"]
                    http_port = node.info["http_port"]
                    LOG.debug("checking node full, %s:%s", http_host, http_port)
                    url = "http://%s:%s/status/full" % (http_host, http_port)
                    request = HTTPRequest(url = url, method = "GET")
                    try:
                        r = yield self.async_client.fetch(request)
                        if r.code == 200:
                            data = json.loads(r.body.decode("utf-8"))
                            if data["result"] == Errors.OK:
                                if not data["full"]:
                                    result = node
                                    self.current_select_index += 1
                                    break
                        else:
                            LOG.error("checking node full failed, %s", url)
                    except ConnectionRefusedError as e:
                        LOG.warning("Scheduler.select_node_balanced: GET %s, %s", url, e)
        except Exception as e:
            LOG.exception(e)
        raise gen.Return(result)

    def select_executable_action(self):
        result = None
        try:
            for action in self.pending_actions:
                if set(action["condition"]).issubset(set(self.tasks[action["task_id"]]["finished"].keys())):
                    for condition_name in action["condition"]:
                        if "input_data" not in action:
                            action["input_data"] = {condition_name: self.tasks[action["task_id"]]["finished"][condition_name]["result"]["data"]}
                        else:
                            action["input_data"][condition_name] = self.tasks[action["task_id"]]["finished"][condition_name]["result"]["data"]
                    result = action
                    break
        except Exception as e:
            LOG.exception(e)
        return result

    def can_load_more_task(self):
        result = False
        try:
            executable_action = self.select_executable_action()
            if executable_action is None and len(self.running_actions) < Connection.total_action_slots:
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def schedule_finish_action(self):
        try:
            for action in self.running_actions:
                pass
        except Exception as e:
            LOG.exception(e)

    def get_running_actions(self, task_id):
        result = []
        try:
            for action in self.running_actions:
                if action["task_id"] == task_id:
                    result.append(action)
        except Exception as e:
            LOG.exception(e)
        return result

    def update_running_action(self, action_data):
        try:
            action_running = None
            now = datetime.datetime.now()
            task_id = action_data["task_id"]
            action_name = action_data["name"]
            for action in self.running_actions:
                if action["task_id"] == task_id and action["name"] == action_name:
                    action["update_at"] = str(now)
                    break
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
                    if "actions" in action_result["result"]:
                        to_actions = {}
                        for action in action_result["result"]["actions"]:
                            self.tasks[task_id]["condition"].append(action["name"])
                            action["task_id"] = task_id
                            action["app_id"] = self.tasks[task_id]["app_info"]["application_id"]
                            action["app_sha1"] = self.tasks[task_id]["app_info"]["sha1"]
                            if "to_action" in action:
                                if action["to_action"] in to_actions:
                                    to_actions[action["to_action"]].append(action["name"])
                                else:
                                    to_actions[action["to_action"]] = [action["name"]]
                            self.pending_actions.append(action)
                        for action in self.pending_actions:
                            if action["name"] in to_actions.keys():
                                action["condition"].extend(to_actions[action["name"]])
                    self.tasks[task_id]["finished"][action_finish["name"]] = action_result
                    self.running_actions.remove(action_finish)
                    finish_condition = self.tasks[task_id]["condition"]
                    current_condition = self.tasks[task_id]["finished"].keys()
                    if len(current_condition) == len(finish_condition):
                        Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.success, "end_at": now, "result": self.tasks[task_id]["finished"]})
                        del self.tasks[task_id]
                    else:
                        Tasks.instance().update(task_id, {"result": self.tasks[task_id]["finished"]})
                else:
                    self.tasks[task_id]["finished"][action_finish["name"]] = action_result
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
                    if "signal" in action_finish:
                        Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.kill, "end_at": now, "result": self.tasks[task_id]["finished"]})
                    else:
                        Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.fail, "end_at": now, "result": self.tasks[task_id]["finished"]})
                    del self.tasks[task_id]
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def stop_task(self, task_id, signal):
        LOG.info("stop task_id: %s, signal: %s", task_id, signal)
        result = False
        try:
            now = datetime.datetime.now()
            pending_actions_tmp = []
            for action in self.pending_actions:
                if action["task_id"] != task_id:
                    pending_actions_tmp.append(action)
            self.pending_actions = pending_actions_tmp
            signal_actions = []
            for action in self.running_actions:
                if action["task_id"] == task_id:
                    action["signal"] = signal
                    signal_actions.append(action)
            if signal_actions:
                for action in signal_actions:
                    url = "http://%s/action/stop" % action["node"]
                    request = HTTPRequest(url = url, method = "PUT", body = json.dumps(action))
                    r = yield self.async_client.fetch(request)
                    if r.code == 200 and json.loads(r.body.decode("utf-8"))["result"] == Errors.OK:
                        LOG.debug("send signal[%s] to action[%s][%s] success", action["signal"], action["task_id"], action["name"])
                    else:
                        raise OperationError("request node[%s] for action[%s][%s] failed" % (url, action["task_id"], action["name"]))
                self.tasks[task_id][Stage.stopping] = True
                Tasks.instance().update(task_id, {"stage": Stage.stopping})
            else:
                Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.kill, "end_at": now, "result": self.tasks[task_id]["finished"]})
                del self.tasks[task_id]
            result = True
        except OperationError as e:
            LOG.error(e)
        except Exception as e:
            LOG.exception(e)
        return result

    def repending_running_actions(self, node_id):
        LOG.warning("repending running actions on node[node_id: %s]", node_id)
        try:
            running_actions_tmp = []
            for action in self.running_actions:
                if action["node_id"] != node_id:
                    running_actions_tmp.append(action)
                else:
                    self.pending_actions.append(action)
            self.running_actions = running_actions_tmp
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def execute_service(self):
        LOG.debug("execute_service")
        try:
            node = yield self.select_node_balanced() 
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
                        action["node_id"] = node.info["node_id"]
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
            load_more_task = self.can_load_more_task()
            LOG.debug("can load more task: %s", load_more_task)
            if load_more_task:
                task_info = Tasks.instance().get_first()
                if task_info:
                    task_id = task_info["task_id"]
                    app_id = task_info["application_id"]
                    app_info = Applications.instance().get(app_id)
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
                                if len(action["condition"]) == 0:
                                    action["input_data"] = task_info["input_data"]
                                finish_condition.append(action["name"])
                                self.pending_actions.append(action)
                            self.tasks[task_id] = {"task_info": task_info, "condition": finish_condition, "app_info": app_info, "finished": {}}
                            Tasks.instance().update(task_id, {"stage": Stage.running, "start_at": datetime.datetime.now()})
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
                Tasks.instance().update(task_id, {"stage": Stage.pending})
            LOG.debug("Scheduler close")
        except Exception as e:
            LOG.exception(e)
