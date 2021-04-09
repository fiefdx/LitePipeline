# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from litepipeline.viewer.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.viewer.config import CONFIG

LOG = logging.getLogger("__name__")


class VenvHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.render(
            "venv/venv.html",
            current_nav = "venv",
            manager_host = "%s:%s" % (
                CONFIG["manager_http_host"],
                CONFIG["manager_http_port"])
        )


class VenvInfoHandler(BaseHandler):
    @gen.coroutine
    def get(self, venv_id):
        self.render(
            "venv/venv_info.html",
            venv_id = venv_id,
            manager_host = "%s:%s" % (
                CONFIG["manager_http_host"],
                CONFIG["manager_http_port"])
        )
