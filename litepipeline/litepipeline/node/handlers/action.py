# -*- coding: utf-8 -*-

import os
import io
import re
import json
import time
import logging
import tarfile

import requests
from tornado import web
from tornado import gen
from tornado import httpclient

from litepipeline.node.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.node.utils.executor import Executor
from litepipeline.node.utils.common import Errors, file_sha1sum
from litepipeline.node.config import CONFIG

LOG = logging.getLogger("__name__")


class RunActionHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            app_id = self.get_json_argument("app_id", "")
            if task_id and app_id:
                Executor.instance().push_action_with_counter(self.json_data)
            LOG.debug("RunActionHandler, task_id: %s, app_id: %s, data: %s", task_id, app_id, self.json_data)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class StopActionHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            name = self.get_json_argument("name", "")
            signal = int(self.get_json_argument("signal", -15))
            if task_id and name:
                success = Executor.instance().stop_action(task_id, name, signal)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
            LOG.debug("StopActionHandler, task_id: %s, data: %s", task_id, self.json_data)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class FullStatusHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK, "full": True}
        try:
            full = Executor.instance().is_full()
            result["full"] = full
            LOG.debug("FullStatusHandler, full: %s", full)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
