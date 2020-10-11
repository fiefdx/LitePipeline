# -*- coding: utf-8 -*-

import os
import json
import logging
import time
import datetime
from copy import deepcopy

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.ioloop
import tornado.web
from tornado import gen

from litepipeline.manager.models.tasks import Tasks
from litepipeline.manager.models.schedules import Schedules
from litepipeline.manager.models.workflows import Workflows
from litepipeline.manager.models.works import Works
from litepipeline.manager.models.services import Services
from litepipeline.manager.utils.app_manager import AppManager
from litepipeline.manager.utils.listener import Connection
from litepipeline.manager.utils.common import Errors, Stage, Status, Event, OperationError, Signal
from litepipeline.manager.config import CONFIG
from litepipeline.manager import logger

LOG = logging.getLogger(__name__)


class Scheduler(object):
    _instance = None
    name = "scheduler"

    def __new__(cls, interval = 1):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.interval = interval
            cls._instance.ioloop_service()
            cls._instance.running_actions = []
            cls._instance.pending_actions = []
            cls._instance.abandoned_actions = []
            cls._instance.tasks = {}
            cls._instance.tasks_stopping = {}
            cls._instance.async_client = AsyncHTTPClient()
            cls._instance.current_select_index = 0
            cls._instance.stop = False
            cls._instance.service_init = True
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
            self.execute_service_support_filters, 
            self.interval * 1000
        )
        self.periodic_execute.start()
        self.periodic_crontab = tornado.ioloop.PeriodicCallback(
            self.crontab_service, 
            30 * 1000 # 30 seconds
        )
        self.periodic_crontab.start()
        self.periodic_work = tornado.ioloop.PeriodicCallback(
            self.work_service, 
            self.interval * 1000
        )
        self.periodic_work.start()
        self.periodic_service = tornado.ioloop.PeriodicCallback(
            self.service_service, 
            self.interval * 1000
        )
        self.periodic_service.start()

    @gen.coroutine
    def select_node(self, filters = {}):
        result = None
        try:
            LOG.debug("clients_dict: %s, total_action_slots: %s", Connection.clients_dict, Connection.total_action_slots)
            for node in Connection.clients:
                filters_success = 0
                for f in filters:
                    if f == "node_id":
                        if node.info["node_id"] == filters[f]:
                            filters_success += 1
                        else:
                            break
                    elif f == "node_ip":
                        if node.info["http_host"] == filters[f]:
                            filters_success += 1
                        else:
                            break
                    elif f == "platform":
                        if node.info["platform"].lower() == filters[f].lower():
                            filters_success += 1
                        else:
                            break
                    elif f == "docker_support":
                        if node.info["docker_support"] == filters[f]:
                            filters_success += 1
                        else:
                            break
                if filters_success == len(filters):
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

    @gen.coroutine
    def select_executable_action_node(self):
        result_action = None
        result_node = None
        try:
            for action in self.pending_actions:
                if "target_env" in action and action["target_env"]: # execute by specific node
                    node = yield self.select_node(filters = action["target_env"])
                    if node and action["name"] in Event.events:
                        result_action = action
                        break
                    elif node and set(action["condition"]).issubset(set(self.tasks[action["task_id"]]["finished"].keys())):
                        for condition_name in action["condition"]:
                            if "input_data" not in action:
                                action["input_data"] = {condition_name: self.tasks[action["task_id"]]["finished"][condition_name]["result"]["data"]}
                            else:
                                action["input_data"][condition_name] = self.tasks[action["task_id"]]["finished"][condition_name]["result"]["data"]
                        result_action = action
                        result_node = node
                        break
                else:
                    if action["name"] in Event.events:
                        result_action = action
                        break
                    elif set(action["condition"]).issubset(set(self.tasks[action["task_id"]]["finished"].keys())):
                        for condition_name in action["condition"]:
                            if "input_data" not in action:
                                action["input_data"] = {condition_name: self.tasks[action["task_id"]]["finished"][condition_name]["result"]["data"]}
                            else:
                                action["input_data"][condition_name] = self.tasks[action["task_id"]]["finished"][condition_name]["result"]["data"]
                        result_action = action
                        break
        except Exception as e:
            LOG.exception(e)
        raise gen.Return([result_action, result_node])

    @gen.coroutine
    def select_task_node_info(self, task_id, action_name):
        result = {"result": Errors.OK}
        try:
            task_info = Tasks.instance().get(task_id)
            if "result" in task_info and action_name in task_info["result"]:
                action_info = task_info["result"][action_name]
                if "node_id" in action_info and action_info["node_id"]:
                    if "stage" in action_info and action_info["stage"] == Stage.finished:
                        node_id = action_info["node_id"]
                        if node_id in Connection.clients_dict:
                            node = Connection.clients_dict[node_id]
                            result["node_info"] = node.info
                            result["task_info"] = task_info
                        else:
                            Errors.set_result_error("NodeNotExists", result)
                    else:
                        Errors.set_result_error("ActionNotFinished", result)
                else:
                    Errors.set_result_error("ActionNoNodeId", result)
            else:
                Errors.set_result_error("ActionNotRun", result)
        except Exception as e:
            LOG.exception(e)
        raise gen.Return(result)

    @gen.coroutine
    def delete_task_workspace(self, task_ids):
        result = {"result": Errors.OK, "failed_task_ids": []}
        try:
            task_infos = []
            for task_id in task_ids:
                task_info = Tasks.instance().get(task_id)
                task_infos.append({"task_id": task_id, "create_at": task_info["create_at"]})
            for node in Connection.clients:
                node_id = node.info["node_id"]
                http_host = node.info["http_host"]
                http_port = node.info["http_port"]
                LOG.debug("delete task_ids: %s workspace from node: %s(%s:%s)", task_ids, node_id, http_host, http_port)
                url = "http://%s:%s/workspace/delete" % (http_host, http_port)
                request = HTTPRequest(url = url, method = "PUT", body = json.dumps({"task_infos": task_infos}))
                r = yield self.async_client.fetch(request)
                if r.code == 200:
                    result_node = json.loads(r.body.decode("utf-8"))
                    if "failed_task_ids" in result_node:
                        result["failed_task_ids"].extend(result_node["failed_task_ids"])
                    LOG.debug("delete workspace from node: %s(%s:%s), result: %s", node_id, http_host, http_port, result_node)
                else:
                    Errors.set_result_error("OperationFailed", result)
                    LOG.warning("delete workspace from node: %s(%s:%s) failed", node_id, http_host, http_port)
                break
        except Exception as e:
            LOG.exception(e)
        raise gen.Return(result)

    @gen.coroutine
    def pack_task_workspace(self, task_id, action_name, force = False):
        result = {"result": Errors.OK}
        try:
            task_info = Tasks.instance().get(task_id)
            create_at = task_info["create_at"]
            if "result" in task_info and action_name in task_info["result"]:
                action_info = task_info["result"][action_name]
                if "node_id" in action_info and action_info["node_id"]:
                    if "stage" in action_info and action_info["stage"] == Stage.finished:
                        node_id = action_info["node_id"]
                        if node_id in Connection.clients_dict:
                            node = Connection.clients_dict[node_id]
                            http_host = node.info["http_host"]
                            http_port = node.info["http_port"]
                            LOG.debug("pack task_id: %s, action: %s workspace from node: %s(%s:%s)", task_id, action_name, node_id, http_host, http_port)
                            url = "http://%s:%s/workspace/pack" % (http_host, http_port)
                            request = HTTPRequest(url = url, method = "PUT", body = json.dumps({"task_id": task_id, "create_at": create_at, "name": action_name, "force": force}))
                            r = yield self.async_client.fetch(request)
                            if r.code == 200:
                                result = json.loads(r.body.decode("utf-8"))
                                LOG.debug("pack workspace from node: %s(%s:%s), result: %s", node_id, http_host, http_port, result)
                            else:
                                Errors.set_result_error("OperationFailed", result)
                                LOG.warning("pack workspace from node: %s(%s:%s) failed", node_id, http_host, http_port)
                        else:
                            Errors.set_result_error("NodeNotExists", result)
                    else:
                        Errors.set_result_error("ActionNotFinished", result)
                else:
                    Errors.set_result_error("ActionNoNodeId", result)
            else:
                Errors.set_result_error("ActionNotRun", result)
        except Exception as e:
            LOG.exception(e)
        raise gen.Return(result)

    def select_executable_action(self):
        result = None
        try:
            for action in self.pending_actions:
                if action["name"] in Event.events:
                    result = action
                    break
                elif set(action["condition"]).issubset(set(self.tasks[action["task_id"]]["finished"].keys())):
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

    def select_abandoned_action(self):
        result = None
        try:
            if self.abandoned_actions:
                result = self.abandoned_actions.pop(0)
        except Exception as e:
            LOG.exception(e)
        return result

    def can_load_more_task(self):
        result = False
        try:
            executable_action = self.select_executable_action()
            if executable_action is None and len(self.running_actions) < Connection.get_total_action_slots():
                result = True
            LOG.debug("can_load_more_task, executable_action: %s, running_actions: %s, total_action_slots: %s", executable_action, len(self.running_actions), Connection.total_action_slots)
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

    def current_schedule_actions(self):
        result = {"running": [], "pending": []}
        try:
            for action in self.running_actions:
                result["running"].append({
                    "task_id": action["task_id"],
                    "work_id": self.tasks[action["task_id"]]["task_info"]["work_id"],
                    "action_name": action["name"],
                    "update_at": str(action["update_at"]) if "update_at" in action else None,
                })
            for action in self.pending_actions:
                result["pending"].append({
                    "task_id": action["task_id"],
                    "work_id": self.tasks[action["task_id"]]["task_info"]["work_id"],
                    "action_name": action["name"],
                    "update_at": str(action["update_at"]) if "update_at" in action else None,
                })
        except Exception as e:
            LOG.exception(e)
        return result

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
                if action_finish["name"] in Event.events: # event actions
                    task_info = Tasks.instance().get(task_id)
                    task_info["result"][action_finish["name"]] = action_result
                    Tasks.instance().update(task_id, {"result": task_info["result"]})
                    self.running_actions.remove(action_finish)
                else: # normal task actions
                    action_info = {"task_create_at": self.tasks[task_id]["task_info"]["create_at"], "task_name": self.tasks[task_id]["task_info"]["task_name"]}
                    work_id = self.tasks[task_id]["task_info"]["work_id"]
                    service_id = self.tasks[task_id]["task_info"]["service_id"]
                    if action_result["status"] == Status.success:
                        if Stage.stopping in self.tasks[task_id] and self.tasks[task_id][Stage.stopping]: # task is stopping                                
                            self.tasks[task_id]["finished"][action_finish["name"]] = action_result
                            self.running_actions.remove(action_finish)
                            Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.kill, "end_at": now, "result": self.tasks[task_id]["finished"]})
                            if Event.fail in self.tasks[task_id]["event_actions"]:
                                action = self.tasks[task_id]["event_actions"][Event.fail]
                                action["input_data"] = self.tasks[task_id]["task_info"]["input_data"]
                                action["input_data"]["result"] = self.tasks[task_id]["finished"]
                                action_info["action_name"] = action["name"]
                                action["input_data"]["action_info"] = action_info
                                self.pending_actions.append(action)
                            if work_id:
                                work_info = Works.instance().get(work_id)
                                if work_info:
                                    if self.tasks[task_id]["task_info"]["task_name"] in Event.events: # event applications
                                        app = work_info["result"][self.tasks[task_id]["task_info"]["task_name"]]
                                        app["stage"] = Stage.finished
                                        app["status"] = Status.kill
                                        Works.instance().update(work_id, {"result": work_info["result"]})
                                    else: # normal applications
                                        app = work_info["result"][self.tasks[task_id]["task_info"]["task_name"]]
                                        app["stage"] = Stage.finished
                                        app["status"] = Status.kill
                                        Works.instance().update(work_id, {"stage": Stage.finished, "status": Status.kill, "end_at": now, "result": work_info["result"]})
                                        if "event_applications" in work_info["configuration"] and Event.fail in work_info["configuration"]["event_applications"]:
                                            event_app = work_info["configuration"]["event_applications"][Event.fail]
                                            input_data = work_info["input_data"] if work_info["input_data"] else {}
                                            input_data.update(work_info["result"])
                                            new_task_id = Tasks.instance().add(
                                                Event.fail,
                                                event_app["app_id"],
                                                stage = Stage.pending,
                                                input_data = input_data,
                                                work_id = work_info["work_id"]
                                            )
                                            if new_task_id:
                                                work_info["result"][Event.fail] = {
                                                    "name": Event.fail,
                                                    "app_id": event_app["app_id"],
                                                    "task_id": new_task_id,
                                                    "stage": Stage.pending,
                                                    "status": None,
                                                }
                                            else:
                                                raise OperationError("create work[%s]'s task failed" % work_info["work_id"])
                                            Works.instance().update(work_id, {"result": work_info["result"]})
                                else:
                                    LOG.warning("work[%s] not exists", work_id)
                            if service_id:
                                service_info = Services.instance().get(service_id)
                                if service_info:
                                    if service_info["task_id"] == task_id:
                                        Services.instance().update(service_id, {"stage": Stage.finished, "status": Status.kill})
                            del self.tasks[task_id]
                        else:
                            if "actions" in action_result["result"]: # dynamic actions
                                to_actions = {}
                                for action in action_result["result"]["actions"]:
                                    if action["name"] not in self.tasks[task_id]["condition"]:
                                        self.tasks[task_id]["condition"].append(action["name"])
                                    action["task_id"] = task_id
                                    action["app_id"] = self.tasks[task_id]["app_info"]["application_id"]
                                    action["app_sha1"] = self.tasks[task_id]["app_info"]["sha1"]
                                    action["task_create_at"] = self.tasks[task_id]["task_info"]["create_at"]
                                    action["input_data"].update(self.tasks[task_id]["task_info"]["input_data"])
                                    action_info["action_name"] = action["name"]
                                    action["input_data"]["action_info"] = action_info
                                    if "to_action" in action:
                                        if action["to_action"] in to_actions:
                                            to_actions[action["to_action"]].append(action["name"])
                                        else:
                                            to_actions[action["to_action"]] = [action["name"]]
                                    if action["name"] not in self.tasks[task_id]["finished"]:
                                        self.pending_actions.append(action)
                                for action in self.pending_actions:
                                    if action["name"] in to_actions.keys():
                                        action["condition"].extend(to_actions[action["name"]])
                            self.tasks[task_id]["finished"][action_finish["name"]] = action_result
                            self.running_actions.remove(action_finish)
                            finish_condition = self.tasks[task_id]["condition"]
                            current_condition = self.tasks[task_id]["finished"].keys()
                            if len(current_condition) == len(finish_condition): # task finish & success
                                Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.success, "end_at": now, "result": self.tasks[task_id]["finished"]})
                                if Event.success in self.tasks[task_id]["event_actions"]:
                                    action = self.tasks[task_id]["event_actions"][Event.success]
                                    action["input_data"] = self.tasks[task_id]["task_info"]["input_data"]
                                    action["input_data"]["result"] = self.tasks[task_id]["finished"]
                                    action_info["action_name"] = action["name"]
                                    action["input_data"]["action_info"] = action_info
                                    self.pending_actions.append(action)
                                if work_id:
                                    work_info = Works.instance().get(work_id)
                                    if work_info:
                                        if self.tasks[task_id]["task_info"]["task_name"] in Event.events: # event applications
                                            app = work_info["result"][self.tasks[task_id]["task_info"]["task_name"]]
                                            app["stage"] = Stage.finished
                                            app["status"] = Status.success
                                            Works.instance().update(work_id, {"result": work_info["result"]})
                                        else: # normal applications
                                            output_action = self.tasks[task_id]["task_info"]["output_action"]
                                            app = work_info["result"][self.tasks[task_id]["task_info"]["task_name"]]
                                            app["stage"] = Stage.finished
                                            app["status"] = Status.success
                                            app["result"] = self.tasks[task_id]["finished"][output_action]["result"]["data"]

                                            work_current_condition = []
                                            for app_name in work_info["result"]:
                                                app = work_info["result"][app_name]
                                                if "stage" in app and app["stage"] == Stage.finished and app["status"] == Status.success:
                                                    work_current_condition.append(app_name)
                                            if len(work_info["configuration"]["applications"]) == len(work_info["result"]): # work finished
                                                Works.instance().update(work_id, {"stage": Stage.finished, "status": Status.success, "end_at": now, "result": work_info["result"]})
                                                if "event_applications" in work_info["configuration"] and Event.success in work_info["configuration"]["event_applications"]:
                                                    event_app = work_info["configuration"]["event_applications"][Event.success]
                                                    input_data = work_info["input_data"] if work_info["input_data"] else {}
                                                    input_data.update(work_info["result"])
                                                    new_task_id = Tasks.instance().add(
                                                        Event.success,
                                                        event_app["app_id"],
                                                        stage = Stage.pending,
                                                        input_data = input_data,
                                                        work_id = work_info["work_id"]
                                                    )
                                                    if new_task_id:
                                                        work_info["result"][Event.success] = {
                                                            "name": Event.success,
                                                            "app_id": event_app["app_id"],
                                                            "task_id": new_task_id,
                                                            "stage": Stage.pending,
                                                            "status": None,
                                                        }
                                                    else:
                                                        raise OperationError("create work[%s]'s task failed" % work_info["work_id"])
                                                    Works.instance().update(work_id, {"result": work_info["result"]})
                                            else: # work running
                                                for app in work_info["configuration"]["applications"]:
                                                    if app["name"] not in work_info["result"] and set(app["condition"]).issubset(set(work_current_condition)):
                                                        input_data = work_info["input_data"] if work_info["input_data"] else {}
                                                        for app_name in app["condition"]:
                                                            input_data[app_name] = work_info["result"][app_name]["result"]
                                                        new_task_id = Tasks.instance().add(
                                                            app["name"],
                                                            app["app_id"],
                                                            stage = Stage.pending,
                                                            input_data = input_data,
                                                            work_id = work_info["work_id"]
                                                        )
                                                        if new_task_id:
                                                            work_info["result"][app["name"]] = {
                                                                "name": app["name"],
                                                                "app_id": app["app_id"],
                                                                "task_id": new_task_id,
                                                                "stage": Stage.pending,
                                                                "status": None,
                                                            }
                                                        else:
                                                            raise OperationError("create work[%s]'s task failed" % work_info["work_id"])
                                                Works.instance().update(work_info["work_id"], {"result": work_info["result"]})
                                    else:
                                        LOG.warning("work[%s] not exists", work_id)
                                if service_id:
                                    service_info = Services.instance().get(service_id)
                                    if service_info:
                                        if service_info["task_id"] == task_id:
                                            Services.instance().update(service_id, {"stage": Stage.finished, "status": Status.success})
                                del self.tasks[task_id]
                            else: # task running
                                Tasks.instance().update(task_id, {"result": self.tasks[task_id]["finished"]})
                    # action failed
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
                            else:
                                self.abandoned_actions.append(action)
                        self.running_actions = running_actions_tmp
                        status = Status.fail # task failed
                        if "signal" in action_finish: # task failed by kill
                            status = Status.kill
                        Tasks.instance().update(task_id, {"stage": Stage.finished, "status": status, "end_at": now, "result": self.tasks[task_id]["finished"]})
                        if Event.fail in self.tasks[task_id]["event_actions"]:
                            action = self.tasks[task_id]["event_actions"][Event.fail]
                            action["input_data"] = self.tasks[task_id]["task_info"]["input_data"]
                            action["input_data"]["result"] = self.tasks[task_id]["finished"]
                            action_info["action_name"] = action["name"]
                            action["input_data"]["action_info"] = action_info
                            self.pending_actions.append(action)
                        if work_id:
                            work_info = Works.instance().get(work_id)
                            if work_info:
                                if self.tasks[task_id]["task_info"]["task_name"] in Event.events: # event applications
                                    app = work_info["result"][self.tasks[task_id]["task_info"]["task_name"]]
                                    app["stage"] = Stage.finished
                                    app["status"] = Status.kill
                                    Works.instance().update(work_id, {"result": work_info["result"]})
                                else: # normal applications
                                    app = work_info["result"][self.tasks[task_id]["task_info"]["task_name"]]
                                    app["stage"] = Stage.finished
                                    app["status"] = status
                                    Works.instance().update(work_id, {"stage": Stage.finished, "status": status, "end_at": now, "result": work_info["result"]})
                                    if "event_applications" in work_info["configuration"] and Event.fail in work_info["configuration"]["event_applications"]:
                                        event_app = work_info["configuration"]["event_applications"][Event.fail]
                                        input_data = work_info["input_data"] if work_info["input_data"] else {}
                                        input_data.update(work_info["result"])
                                        new_task_id = Tasks.instance().add(
                                            Event.fail,
                                            event_app["app_id"],
                                            stage = Stage.pending,
                                            input_data = input_data,
                                            work_id = work_info["work_id"]
                                        )
                                        if new_task_id:
                                            work_info["result"][Event.fail] = {
                                                "name": Event.fail,
                                                "app_id": event_app["app_id"],
                                                "task_id": new_task_id,
                                                "stage": Stage.pending,
                                                "status": None,
                                            }
                                        else:
                                            raise OperationError("create work[%s]'s task failed" % work_info["work_id"])
                                        Works.instance().update(work_id, {"result": work_info["result"]})
                            else:
                                LOG.warning("work[%s] not exists", work_id)
                        if service_id:
                            service_info = Services.instance().get(service_id)
                            if service_info:
                                if service_info["task_id"] == task_id:
                                    Services.instance().update(service_id, {"stage": Stage.finished, "status": status})
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
                        raise OperationError("request node[%s] for stopping action[%s][%s] failed" % (url, action["task_id"], action["name"]))
                self.tasks[task_id][Stage.stopping] = True
                Tasks.instance().update(task_id, {"stage": Stage.stopping})
            else:
                task_name = ""
                work_id = ""
                service_id = ""
                if task_id in self.tasks:
                    work_id = self.tasks[task_id]["task_info"]["work_id"]
                    service_id = self.tasks[task_id]["task_info"]["service_id"]
                    task_name = self.tasks[task_id]["task_info"]["task_name"]
                    Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.kill, "end_at": now, "result": self.tasks[task_id]["finished"]})
                    del self.tasks[task_id]
                else:
                    task_info = Tasks.instance().get(task_id)
                    if task_info:
                        work_id = task_info["work_id"]
                        service_id = task_info["service_id"]
                        task_name = task_info["task_name"]
                    Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.kill, "end_at": now})
                if work_id:
                    work_info = Works.instance().get(work_id)
                    if work_info:
                        app = work_info["result"][task_name]
                        app["stage"] = Stage.finished
                        app["status"] = Status.kill
                        Works.instance().update(work_id, {"stage": Stage.finished, "status": Status.kill, "end_at": now, "result": work_info["result"]})
                    else:
                        LOG.warning("work[%s] not exists", work_id)
                if service_id:
                    service_info = Services.instance().get(service_id)
                    if service_info:
                        if service_info["task_id"] == task_id:
                            Services.instance().update(service_id, {"stage": Stage.finished, "status": Status.kill})
            result = True
        except OperationError as e:
            LOG.error(e)
        except Exception as e:
            LOG.exception(e)
        return result

    @gen.coroutine
    def cancel_action(self, action):
        result = False
        try:
            url = "http://%s/action/cancel" % action["node"]
            request = HTTPRequest(url = url, method = "PUT", body = json.dumps(action))
            r = yield self.async_client.fetch(request)
            if r.code == 200 and json.loads(r.body.decode("utf-8"))["result"] == Errors.OK:
                LOG.debug("send cancel signal to action[%s][%s] success", action["task_id"], action["name"])
            else:
                raise OperationError("request node[%s] for cancelling action[%s][%s] failed" % (url, action["task_id"], action["name"]))
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
    def execute_service_support_filters(self): # from RAM pending to RAM running
        LOG.debug("execute_service support filters")
        try:
            action, node = yield self.select_executable_action_node()
            LOG.info("selected action: %s", action)
            if action:
                if not node:
                    node = yield self.select_node_balanced() 
                if node:
                    http_host = node.info["http_host"]
                    http_port = node.info["http_port"]
                    LOG.debug("select node: %s:%s", http_host, http_port)
                    action = self.select_executable_action()
                    LOG.info("seleted action: %s", action)
                    if action:
                        if "input_data" in action:
                            action["input_data"]["ldfs_host"] = CONFIG["ldfs_http_host"]
                            action["input_data"]["ldfs_port"] = CONFIG["ldfs_http_port"]
                            if "action_info" in action["input_data"]:
                                action["input_data"]["action_info"]["http_host"] = http_host
                                action["input_data"]["action_info"]["http_port"] = http_port
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
            else:
                LOG.debug("no more executable action")
            abandoned_action = self.select_abandoned_action()
            if abandoned_action:
                task_id = abandoned_action["task_id"]
                app_id = abandoned_action["app_id"]
                action_name = abandoned_action["name"]
                success = yield self.cancel_action(abandoned_action)
                if not success:
                    self.abandoned_actions.append(abandoned_action)
                LOG.info("abandon action, app_id: %s, task_id: %s, action: %s, success: %s", app_id, task_id, action_name, success)
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def execute_service(self): # from RAM pending to RAM running
        LOG.debug("execute_service")
        try:
            if not self.stop:
                node = yield self.select_node_balanced()
                if node:
                    http_host = node.info["http_host"]
                    http_port = node.info["http_port"]
                    LOG.debug("select node: %s:%s", http_host, http_port)
                    action = self.select_executable_action()
                    LOG.info("seleted action: %s", action)
                    if action:
                        if "input_data" in action:
                            action["input_data"]["ldfs_host"] = CONFIG["ldfs_http_host"]
                            action["input_data"]["ldfs_port"] = CONFIG["ldfs_http_port"]
                            if "action_info" in action["input_data"]:
                                action["input_data"]["action_info"]["http_host"] = http_host
                                action["input_data"]["action_info"]["http_port"] = http_port
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
            else:
                LOG.warning("execute_service wait to stop")
            abandoned_action = self.select_abandoned_action()
            if abandoned_action:
                task_id = abandoned_action["task_id"]
                app_id = abandoned_action["app_id"]
                action_name = abandoned_action["name"]
                success = yield self.cancel_action(abandoned_action)
                if not success:
                    self.abandoned_actions.append(abandoned_action)
                LOG.info("abandon action, app_id: %s, task_id: %s, action: %s, success: %s", app_id, task_id, action_name, success)
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def schedule_service(self): # from database pending / recovering to RAM pending
        LOG.debug("schedule_service")
        try:
            if not self.stop:
                load_more_task = self.can_load_more_task()
                LOG.debug("can load more task: %s", load_more_task)
                if load_more_task:
                    task_info = Tasks.instance().get_first()
                    if task_info:
                        task_id = task_info["task_id"]
                        app_id = task_info["application_id"]
                        app_info = AppManager.instance().info(app_id)
                        if app_info:
                            app_config = AppManager.instance().get_app_config(app_id, app_info["sha1"])
                            if app_config:
                                finish_condition = []
                                task_info["output_action"] = app_config["output_action"]
                                if task_info["stage"] == Stage.pending: # load pending task
                                    for action in app_config["actions"]:
                                        action["task_id"] = task_id
                                        action["app_id"] = app_id
                                        action["app_sha1"] = app_info["sha1"]
                                        action["task_create_at"] = task_info["create_at"]
                                        action["input_data"] = deepcopy(task_info["input_data"])
                                        action["input_data"]["action_info"] = {}
                                        action["input_data"]["action_info"]["task_create_at"] = task_info["create_at"]
                                        action["input_data"]["action_info"]["task_name"] = task_info["task_name"]
                                        action["input_data"]["action_info"]["action_name"] = action["name"]
                                        action["docker_registry"] = CONFIG["docker_registry"]
                                        if "target_env" in action["input_data"] and action["input_data"]["target_env"] and action["name"] in action["input_data"]["target_env"]:
                                            if "target_env" not in action:
                                                action["target_env"] = {}
                                            action["target_env"].update(action["input_data"]["target_env"][action["name"]])
                                        finish_condition.append(action["name"])
                                        self.pending_actions.append(action)
                                    event_actions = {}
                                    if "event_actions" in app_config:
                                        for event_name in app_config["event_actions"]:
                                            action = app_config["event_actions"][event_name]
                                            action["name"] = event_name
                                            action["condition"] = []
                                            action["task_id"] = task_id
                                            action["app_id"] = app_id
                                            action["app_sha1"] = app_info["sha1"]
                                            action["task_create_at"] = task_info["create_at"]
                                            action["docker_registry"] = CONFIG["docker_registry"]
                                        event_actions = app_config["event_actions"]
                                    self.tasks[task_id] = {"task_info": task_info, "condition": finish_condition, "app_info": app_info, "finished": {}, "event_actions": event_actions}
                                    Tasks.instance().update(task_id, {"stage": Stage.running, "start_at": datetime.datetime.now()})
                                    work_id = task_info["work_id"]
                                    if work_id:
                                        work_info = Works.instance().get(work_id)
                                        if work_info:
                                            if task_info["task_name"] in work_info["result"]:
                                                work_info["result"][task_info["task_name"]]["stage"] = Stage.running
                                                Works.instance().update(work_id, {"result": work_info["result"]})
                                    service_id = task_info["service_id"]
                                    if service_id:
                                        service_info = Services.instance().get(service_id)
                                        if service_info:
                                            if service_info["task_id"] == task_id:
                                                Services.instance().update(service_id, {"stage": Stage.running})
                                elif task_info["stage"] == Stage.recovering: # load recovering task
                                    actions_tmp = {}
                                    for action in app_config["actions"]: # load configuration actions
                                        action["task_id"] = task_id
                                        action["app_id"] = app_id
                                        action["app_sha1"] = app_info["sha1"]
                                        action["task_create_at"] = task_info["create_at"]
                                        action["input_data"] = deepcopy(task_info["input_data"])
                                        action["input_data"]["action_info"] = {}
                                        action["input_data"]["action_info"]["task_create_at"] = task_info["create_at"]
                                        action["input_data"]["action_info"]["task_name"] = task_info["task_name"]
                                        action["input_data"]["action_info"]["action_name"] = action["name"]
                                        action["docker_registry"] = CONFIG["docker_registry"]
                                        if "target_env" in action["input_data"] and action["input_data"]["target_env"] and action["name"] in action["input_data"]["target_env"]:
                                            if "target_env" not in action:
                                                action["target_env"] = {}
                                            action["target_env"].update(action["input_data"]["target_env"][action["name"]])
                                        finish_condition.append(action["name"])
                                        actions_tmp[action["name"]] = action
                                    event_actions = {}
                                    if "event_actions" in app_config:
                                        for event_name in app_config["event_actions"]:
                                            action = app_config["event_actions"][event_name]
                                            action["name"] = event_name
                                            action["condition"] = []
                                            action["task_id"] = task_id
                                            action["app_id"] = app_id
                                            action["app_sha1"] = app_info["sha1"]
                                            action["task_create_at"] = task_info["create_at"]
                                            action["docker_registry"] = CONFIG["docker_registry"]
                                        event_actions = app_config["event_actions"]
                                    task_result = {}
                                    actions_dynamic = []
                                    for action_name in task_info["result"]: # load result actions
                                        action = task_info["result"][action_name]
                                        if action["stage"] == Stage.finished and action["status"] == Status.success:
                                            if action_name in actions_tmp: # remove success action
                                                del actions_tmp[action_name]
                                            task_result[action_name] = action
                                            if "actions" in action["result"] and action["result"]["actions"]:
                                                actions_dynamic.extend(action["result"]["actions"])
                                    for action in actions_dynamic: # load dynamic actions
                                        to_action = action["to_action"] if "to_action" in action and action["to_action"] else None
                                        if to_action and to_action in actions_tmp:
                                            actions_tmp[to_action]["condition"].append(action["name"])
                                        if action["name"] not in task_result: # failed dynamic action, append into actions_tmp
                                            action["task_id"] = task_id
                                            action["app_id"] = app_id
                                            action["app_sha1"] = app_info["sha1"]
                                            action["task_create_at"] = task_info["create_at"]
                                            action["input_data"]["action_info"] = {}
                                            action["input_data"]["action_info"]["task_create_at"] = task_info["create_at"]
                                            action["input_data"]["action_info"]["task_name"] = task_info["task_name"]
                                            action["input_data"]["action_info"]["action_name"] = action["name"]
                                            action["docker_registry"] = CONFIG["docker_registry"]
                                            if "target_env" in action["input_data"] and action["input_data"]["target_env"] and action["name"] in action["input_data"]["target_env"]:
                                                if "target_env" not in action:
                                                    action["target_env"] = {}
                                                action["target_env"].update(action["input_data"]["target_env"][action["name"]])
                                            if "signal" in action:
                                                del action["signal"]
                                            actions_tmp[action["name"]] = action
                                        finish_condition.append(action["name"])
                                    for name in actions_tmp:
                                        self.pending_actions.append(actions_tmp[name])
                                    self.tasks[task_id] = {"task_info": task_info, "condition": finish_condition, "app_info": app_info, "finished": task_result, "event_actions": event_actions}
                                    LOG.debug("recover task, task_id: %s, condition: %s, finished: %s", task_id, finish_condition, task_result)
                                    Tasks.instance().update(task_id, {"stage": Stage.running, "start_at": datetime.datetime.now()})
                                    work_id = task_info["work_id"]
                                    if work_id:
                                        work_info = Works.instance().get(work_id)
                                        if work_info:
                                            if task_info["task_name"] in work_info["result"]:
                                                work_info["result"][task_info["task_name"]]["stage"] = Stage.running
                                                Works.instance().update(work_id, {"result": work_info["result"]})
                                    service_id = task_info["service_id"]
                                    if service_id:
                                        service_info = Services.instance().get(service_id)
                                        if service_info:
                                            if service_info["task_id"] == task_id:
                                                Services.instance().update(service_id, {"stage": Stage.running})
                                else:
                                    LOG.error("unknown task stage value: %s", task_info["stage"])
                            else:
                                Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.error, "result": {"message": "get app[%s:%s] config file failed" % (app_id, app_info["sha1"])}})
                                LOG.error("Scheduler get app[%s:%s] config file failed", app_id, app_info["sha1"])
                        elif app_info is None:
                            Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.error, "result": {"message": "app[%s] not exists" % app_id}})
                            LOG.error("Scheduler task[%s]'s app_info[%s] not exists", task_id, app_id)
                        else:
                            Tasks.instance().update(task_id, {"stage": Stage.finished, "status": Status.error, "result": {"message": "get app[%s] failed" % app_id}})
                            LOG.error("Scheduler get task[%s]'s app_info[%s] failed", task_id, app_id)
                    elif task_info is None:
                        LOG.debug("Scheduler no more task to execute")
                    else:
                        LOG.error("Scheduler get task failed")
                else:
                    LOG.warning("no selectable node")
            else:
                LOG.warning("schedule_service wait to stop")
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def crontab_service(self):
        LOG.debug("crontab_service")
        try:
            schedules = Schedules.instance()
            now = datetime.datetime.now()
            for schedule_id in schedules.cache:
                schedule = schedules.cache[schedule_id]
                executed = False if ("executed" not in schedule) or ("executed" in schedule and schedule["executed"] != str(now.date())) else True
                if not executed:
                    if schedule["day_of_month"] == -1 and schedule["day_of_week"] == -1:
                        hour = 0 if schedule["hour"] == -1 else schedule["hour"]
                        minute = 0 if schedule["minute"] == -1 else schedule["minute"]
                        if now.hour == hour and now.minute >= minute and now.minute - minute < 5:
                            if schedule["source"] == Schedules.application:
                                task_id = Tasks.instance().add(schedule["schedule_name"], schedule["source_id"], stage = Stage.pending, input_data = schedule["input_data"])
                                if task_id:
                                    schedule["executed"] = str(now.date())
                                else:
                                    LOG.error("execute schedule every day failed: %s, at: %s, task_id: %s", schedule, now, task_id)
                                LOG.debug("execute schedule every day: %s, at: %s, task_id: %s", schedule, now, task_id)
                            elif schedule["source"] == Schedules.workflow:
                                workflow = Workflows.instance().get(schedule["source_id"])
                                if workflow:
                                    work_id = Works.instance().add(schedule["schedule_name"], schedule["source_id"], stage = Stage.pending, input_data = schedule["input_data"], configuration = workflow["configuration"])
                                    if work_id:
                                        schedule["executed"] = str(now.date())
                                    else:
                                        LOG.error("execute schedule every day failed: %s, at: %s, work_id: %s", schedule, now, work_id)
                                    LOG.debug("execute schedule every day: %s, at: %s, work_id: %s", schedule, now, work_id)
                    elif schedule["day_of_month"] != -1 and schedule["day_of_month"] == now.day:
                        hour = 0 if schedule["hour"] == -1 else schedule["hour"]
                        minute = 0 if schedule["minute"] == -1 else schedule["minute"]
                        if now.hour == hour and now.minute >= minute and now.minute - minute < 5:
                            if schedule["source"] == Schedules.application:
                                task_id = Tasks.instance().add(schedule["schedule_name"], schedule["source_id"], stage = Stage.pending, input_data = schedule["input_data"])
                                if task_id:
                                    schedule["executed"] = str(now.date())
                                else:
                                    LOG.error("execute schedule every month failed: %s, at: %s, task_id: %s", schedule, now, task_id)
                                LOG.debug("execute schedule every month: %s, at: %s, task_id: %s", schedule, now, task_id)
                            elif schedule["source"] == Schedules.workflow:
                                workflow = Workflows.instance().get(schedule["source_id"])
                                if workflow:
                                    work_id = Works.instance().add(schedule["schedule_name"], schedule["source_id"], stage = Stage.pending, input_data = schedule["input_data"], configuration = workflow["configuration"])
                                    if work_id:
                                        schedule["executed"] = str(now.date())
                                    else:
                                        LOG.error("execute schedule every month failed: %s, at: %s, work_id: %s", schedule, now, work_id)
                                    LOG.debug("execute schedule every month: %s, at: %s, work_id: %s", schedule, now, work_id)
                    elif schedule["day_of_week"] != -1 and schedule["day_of_week"] == now.isoweekday():
                        hour = 0 if schedule["hour"] == -1 else schedule["hour"]
                        minute = 0 if schedule["minute"] == -1 else schedule["minute"]
                        if now.hour == hour and now.minute >= minute and now.minute - minute < 5:
                            if schedule["source"] == Schedules.application:
                                task_id = Tasks.instance().add(schedule["schedule_name"], schedule["source_id"], stage = Stage.pending, input_data = schedule["input_data"])
                                if task_id:
                                    schedule["executed"] = str(now.date())
                                else:
                                    LOG.error("execute schedule every week failed: %s, at: %s, task_id: %s", schedule, now, task_id)
                                LOG.debug("execute schedule every week: %s, at: %s, task_id: %s", schedule, now, task_id)
                            elif schedule["source"] == Schedules.workflow:
                                workflow = Workflows.instance().get(schedule["source_id"])
                                if workflow:
                                    work_id = Works.instance().add(schedule["schedule_name"], schedule["source_id"], stage = Stage.pending, input_data = schedule["input_data"], configuration = workflow["configuration"])
                                    if work_id:
                                        schedule["executed"] = str(now.date())
                                    else:
                                        LOG.error("execute schedule every week failed: %s, at: %s, work_id: %s", schedule, now, work_id)
                                    LOG.debug("execute schedule every week: %s, at: %s, work_id: %s", schedule, now, work_id)
                else:
                    LOG.debug("executed schedule: %s", schedule)
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def service_service(self):
        LOG.debug("service_service")
        try:
            services = Services.instance()
            now = datetime.datetime.now()
            if self.stop:
                if len(self.tasks) > 0 and len(self.tasks_stopping) == 0:
                    self.tasks_stopping = deepcopy(self.tasks)
                    for task_id in self.tasks_stopping:
                        yield self.stop_task(task_id, Signal.kill)
            else:
                if self.service_init:
                    LOG.info("init all service")
                    for service_id in services.cache:
                        service = services.cache[service_id]
                        if service["enable"]:
                            task_id = Tasks.instance().add(
                                service["name"],
                                service["application_id"],
                                stage = Stage.pending,
                                input_data = service["input_data"],
                                service_id = service_id
                            )
                            services.update(service_id, {
                                "stage": Stage.pending,
                                "task_id": task_id
                            })
                        else:
                            services.update(service_id, {
                                "stage": Stage.finished,
                                "task_id": "",
                                "status": ""
                            })
                    self.service_init = False
                else:
                    for service_id in services.cache:
                        service = services.cache[service_id]
                        task_id = service["task_id"]
                        if service["enable"] and service["stage"] in ("", Stage.finished):
                            task_id = Tasks.instance().add(
                                service["name"],
                                service["application_id"],
                                stage = Stage.pending,
                                input_data = service["input_data"],
                                service_id = service_id
                            )
                            services.update(service_id, {
                                "stage": Stage.pending,
                                "task_id": task_id,
                                "status": ""
                            })
                        elif not service["enable"] and service["stage"] in (Stage.pending, Stage.recovering, Stage.running) and task_id:
                            yield self.stop_task(task_id, service["signal"])
                        LOG.debug("service: %s", service)
        except Exception as e:
            LOG.exception(e)

    @gen.coroutine
    def work_service(self):
        LOG.debug("work_service")
        try:
            work_info = Works.instance().get_first()
            if work_info:
                if work_info["stage"] == Stage.pending:
                    result = {}
                    for app in work_info["configuration"]["applications"]:
                        if len(app["condition"]) == 0:
                            task_id = Tasks.instance().add(
                                app["name"],
                                app["app_id"],
                                stage = Stage.pending,
                                input_data = work_info["input_data"] if work_info["input_data"] else {},
                                work_id = work_info["work_id"]
                            )
                            if task_id:
                                result[app["name"]] = {
                                    "name": app["name"],
                                    "app_id": app["app_id"],
                                    "task_id": task_id,
                                    "stage": Stage.pending,
                                    "status": None,
                                }
                            else:
                                raise OperationError("create work[%s]'s task failed" % work_info["work_id"])
                elif work_info["stage"] == Stage.recovering:
                    for app_name in work_info["result"]:
                        app = work_info["result"][app_name]
                        if "stage" not in app or ("stage" in app and app["stage"] == Stage.finished and app["status"] in (Status.fail, Status.kill)):
                            app["stage"] = Stage.recovering
                            app["status"] = None
                            task_id = app["task_id"]
                            Tasks.instance().update(task_id, {"stage": Stage.recovering, "status": None})
                    result = work_info["result"]
                Works.instance().update(work_info["work_id"], {"stage": Stage.running, "start_at": datetime.datetime.now(), "result": result})
        except Exception as e:
            LOG.exception(e)

    def close(self):
        try:
            if self.periodic_schedule:
                self.periodic_schedule.stop()
            if self.periodic_crontab:
                self.periodic_crontab.stop()
            if self.periodic_work:
                self.periodic_work.stop()
            if self.periodic_execute:
                self.periodic_execute.stop()
            if self.periodic_service:
                self.periodic_service.stop()
            for task_id in self.tasks_stopping:
                task_info = self.tasks_stopping[task_id]["task_info"]
                if not task_info["service_id"]:
                    Tasks.instance().update(task_id, {"stage": Stage.recovering})
                else:
                    Services.instance().update(task_info["service_id"], {"stage": "", "status": "", "task_id": ""})
            LOG.debug("Scheduler close")
        except Exception as e:
            LOG.exception(e)
