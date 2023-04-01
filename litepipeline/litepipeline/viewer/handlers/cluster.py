# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from litepipeline.viewer.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.viewer.utils.common import encode_token
from litepipeline.viewer.config import CONFIG

LOG = logging.getLogger("__name__")


class ClusterHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.render(
            "cluster/cluster.html",
            current_nav = "cluster",
            manager_host = "%s:%s" % (
                self.get_manager_http_host(),
                CONFIG["manager_http_port"]),
            user = CONFIG["manager_user"],
            token = encode_token(CONFIG["manager_user"], CONFIG["manager_password"])
        )
