# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from litepipeline.viewer.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.viewer.config import CONFIG

LOG = logging.getLogger("__name__")


class WorkflowHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.render(
            "workflow/workflow.html",
            current_nav = "workflow",
            manager_host = "%s:%s" % (
                CONFIG["manager_http_host"],
                CONFIG["manager_http_port"])
        )
