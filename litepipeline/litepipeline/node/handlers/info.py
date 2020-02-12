# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from litepipeline.node.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.node.config import CONFIG

LOG = logging.getLogger("__name__")


class AboutHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"message": "LitePipeline node service"}
        self.write(result)
        self.finish()
