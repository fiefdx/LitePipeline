# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.manager.models.applications import Applications
from litepipeline.manager.models.tasks import Tasks
from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, Stage, splitall, JSONLoadError
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
            if app_id and Applications.instance().get(app_id) and task_name:
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
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class StopTaskHandler(BaseHandler): # kill -9 or -15
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            signal = int(self.get_json_argument("signal", -15))
            if task_id and signal in (-9, -15):
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
            stage = self.get_argument("stage", "")
            LOG.debug("ListTaskHandler offset: %s, limit: %s, stage: %s", offset, limit, stage)
            result["tasks"] = Tasks.instance().list(offset = offset, limit = limit, stage = stage)
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
