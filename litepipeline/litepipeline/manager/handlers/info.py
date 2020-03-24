# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.utils.listener import Connection
from litepipeline.manager.utils.common import Errors
from litepipeline.version import __version__
from litepipeline.manager.config import CONFIG

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
        result = {"result": Errors.OK, "version": __version__}
        try:
            info = {"number_of_nodes": 0, "nodes": []}
            for node in Connection.clients:
                info["nodes"].append(node.info)
                info["number_of_nodes"] += 1
            result["info"] = info
            result["info"]["actions"] = Scheduler.instance().current_schedule_actions()
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(json.dumps(result, sort_keys = True))
        self.finish()
