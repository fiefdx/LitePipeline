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

from handlers.base import BaseHandler, BaseSocketHandler
from utils.executor import ActionExecutor
from utils.common import Errors, file_sha1sum
from config import CONFIG

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
                ActionExecutor.push_action(self.json_data)
            LOG.debug("RunActionHandler, task_id: %s, app_id: %s, data: %s", task_id, app_id, self.json_data)
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
            full = ActionExecutor.is_full()
            result["full"] = full
            LOG.debug("FullStatusHandler, full: %s", full)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
