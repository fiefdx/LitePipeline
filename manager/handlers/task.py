# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from handlers.base import BaseHandler, BaseSocketHandler
from models.applications import ApplicationsDB
from models.tasks import TasksDB
from utils.scheduler import TaskScheduler
from utils.common import file_sha1sum, file_md5sum, Errors, splitall, JSONLoadError
from config import CONFIG

LOG = logging.getLogger("__name__")


class CreateTaskHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_name = self.get_json_argument("task_name", "")
            app_id = self.get_json_argument("app_id", "")
            source = self.get_json_argument("source", {})
            if app_id and ApplicationsDB.get(app_id) and task_name:
                source_data = {}
                if isinstance(source, dict):
                    source_data = source
                else:
                    raise JSONLoadError("source must be dict type")
                task_id = TasksDB.add(task_name, app_id, source = source)
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
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class DeleteTaskHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            task_id = self.get_argument("task_id", "")
            if task_id:
                success = TasksDB.delete(task_id)
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
                task_info = TasksDB.get(task_id)
                if task_info:
                    result["task_info"] = task_info
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
            LOG.debug("ListTaskHandler offset: %s, limit: %s", offset, limit)
            result["tasks"] = TasksDB.list(offset = offset, limit = limit)
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
            if task_id and name:
                TaskScheduler.update_finish_action(self.json_data)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("UpdateActionHandler, action_name: %s, task_id: %s", name, task_id)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
