# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from handlers.base import BaseHandler, BaseSocketHandler
from utils.listener import Connection
from utils.common import Errors
from config import CONFIG

LOG = logging.getLogger("__name__")


class AboutHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"message": "LitePipeline manager service"}
        self.write(result)
        self.finish()


class ClusterInfoHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            info = {"number_of_nodes": 0, "nodes": []}
            for node in Connection.clients:
                info["nodes"].append(node.info)
                info["number_of_nodes"] += 1
            result["info"] = info
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(json.dumps(result, sort_keys = True))
        self.finish()
