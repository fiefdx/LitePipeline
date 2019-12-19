# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from handlers.base import BaseHandler, BaseSocketHandler
from utils.listener import Connection
from config import CONFIG

LOG = logging.getLogger("__name__")


class DeployHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"message": "deploy handler"}
        self.write(result)
        self.finish()

    @gen.coroutine
    def post(self):
        pass
