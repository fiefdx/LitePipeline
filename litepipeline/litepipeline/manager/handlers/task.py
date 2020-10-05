# -*- coding: utf-8 -*-

import json
import time
import urllib
import logging

from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.manager.models.tasks import Tasks
from litepipeline.manager.utils.app_manager import AppManager
from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, Stage, Status, Signal, splitall, JSONLoadError
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class CreateTaskHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_name = self.get_json_argument("task_name", "")
            app_id = self.get_json_argument("app_id", "")
            input_data = self.get_json_argument("input_data", {})
            if app_id and AppManager.instance().info(app_id) and task_name:
                if not isinstance(input_data, dict):
                    raise JSONLoadError("input_data must be dict type")
                task_id = Tasks.instance().add(task_name, app_id, input_data = input_data)
                if task_id is not False:
                    result["task_id"] = task_id
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("CreateTaskHandler, task_name: %s, app_id: %s", task_name, app_id)
        except JSONLoadError as e:
            LOG.error(e)
            Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class RunTaskHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            if task_id:
                task = Tasks.instance().get(task_id)
                if task:
                    if task["stage"] == Stage.finished:
                        success = Tasks.instance().update(task_id, {"stage": Stage.pending, "status": None})
                        if not success:
                            Errors.set_result_error("OperationFailed", result)
                    else:
                        Errors.set_result_error("TaskStillRunning", result)
                elif task is None:
                    Errors.set_result_error("TaskNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("RunTaskHandler, task_id: %s", task_id)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class RecoverTaskHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            if task_id:
                task = Tasks.instance().get(task_id)
                if task:
                    if task["stage"] == Stage.finished:
                        if task["status"] != Status.success:
                            success = Tasks.instance().update(task_id, {"stage": Stage.recovering, "status": None})
                            if not success:
                                Errors.set_result_error("OperationFailed", result)
                        else:
                            Errors.set_result_error("TaskAlreadySuccess", result)
                    else:
                        Errors.set_result_error("TaskStillRunning", result)
                elif task is None:
                    Errors.set_result_error("TaskNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("RecoverTaskHandler, task_id: %s", task_id)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class StopTaskHandler(BaseHandler): # kill -9 or -15
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            signal = int(self.get_json_argument("signal", Signal.kill))
            if task_id and signal in (Signal.kill, Signal.terminate):
                task = Tasks.instance().get(task_id)
                if task:
                    if task["stage"] != Stage.finished:
                        success = yield Scheduler.instance().stop_task(task_id, signal)
                        if not success:
                            Errors.set_result_error("OperationFailed", result)
                    else:
                        Errors.set_result_error("TaskAlreadyFinished", result)
                elif task is None:
                    Errors.set_result_error("TaskNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("StopTaskHandler, task_id: %s, signal: %s", task_id, signal)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteTaskHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            task_id = self.get_argument("task_id", "")
            if task_id:
                success = Tasks.instance().delete(task_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteTaskWorkspaceHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_ids = self.get_json_argument("task_ids", [])
            if isinstance(task_ids, list) and task_ids:
                result = yield Scheduler.instance().delete_task_workspace(task_ids)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("DeleteTaskWorkspaceHandler, task_ids: %s", task_ids)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class PackTaskWorkspaceHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            name = self.get_json_argument("name", "")
            force = self.get_json_argument("force", False)
            if task_id and name:
                result = yield Scheduler.instance().pack_task_workspace(task_id, name, force)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("PackTaskWorkspaceHandler, task_id: %s, name: %s", task_id, name)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DownloadTaskWorkspaceHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        redirect_flag = False
        try:
            task_id = self.get_argument("task_id", "")
            name = self.get_argument("name", "")
            if task_id and name:
                r = yield Scheduler.instance().select_task_node_info(task_id, name)
                if "node_info" in r and r["node_info"] and r["task_info"]:
                    http_host = r["node_info"]["http_host"]
                    http_port = r["node_info"]["http_port"]
                    if http_host == "127.0.0.1":
                        host_parts = urllib.parse.urlsplit("//" + self.request.host)
                        http_host = host_parts.hostname
                    create_at = r["task_info"]["create_at"]
                    url = "http://%s:%s/workspace/download?task_id=%s&create_at=%s&name=%s" % (http_host, http_port, task_id, create_at, name)
                    self.redirect(url)
                    redirect_flag = True
                else:
                    result = r
            else:
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        if not redirect_flag:
            self.write(result)
            self.finish()


class InfoTaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            task_id = self.get_argument("task_id", "")
            if task_id:
                task_info = Tasks.instance().get(task_id)
                if task_info:
                    result["task_info"] = task_info
                    if task_info["stage"] == Stage.running:
                        result["task_running_info"] = Scheduler.instance().get_running_actions(task_id)
                elif task_info is None:
                    Errors.set_result_error("TaskNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class ListTaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            filters = {}
            task_id = self.get_argument("task_id", "")
            if task_id:
                filters["task_id"] = task_id
            app_id = self.get_argument("app_id", "")
            if app_id:
                filters["app_id"] = app_id
            work_id = self.get_argument("work_id", "")
            if work_id:
                filters["work_id"] = work_id
            service_id = self.get_argument("service_id", "")
            if service_id:
                filters["service_id"] = service_id
            name = self.get_argument("name", "")
            if name:
                filters["name"] = name
            stage = self.get_argument("stage", "")
            if stage:
                filters["stage"] = stage
            status = self.get_argument("status", "")
            if status:
                filters["status"] = status
            LOG.debug("ListTaskHandler offset: %s, limit: %s, filters: %s", offset, limit, filters)
            r = Tasks.instance().list(offset = offset, limit = limit, filters = filters)
            result["tasks"] = r["tasks"]
            result["total"] = r["total"]
            result["offset"] = offset
            result["limit"] = limit
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class CleanTaskHistoryHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class UpdateActionHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            name = self.get_json_argument("name", "")
            task_id = self.get_json_argument("task_id", "")
            stage = self.get_json_argument("stage", "")
            if task_id and name and stage:
                if stage == Stage.running:
                    Scheduler.instance().update_running_action(self.json_data)
                elif stage == Stage.finished:
                    Scheduler.instance().update_finish_action(self.json_data)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("UpdateActionHandler, action_name: %s, task_id: %s", name, task_id)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
