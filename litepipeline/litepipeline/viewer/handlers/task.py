# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from litepipeline.viewer.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.viewer.config import CONFIG

LOG = logging.getLogger("__name__")


class TaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.render(
            "task/task.html",
            current_nav = "task",
            manager_host = "%s:%s" % (
                CONFIG["manager_http_host"],
                CONFIG["manager_http_port"])
        )


class TaskInfoHandler(BaseHandler):
    @gen.coroutine
    def get(self, task_id):
        self.render(
            "task/task_info.html",
            task_id = task_id,
            manager_host = "%s:%s" % (
                CONFIG["manager_http_host"],
                CONFIG["manager_http_port"])
        )
