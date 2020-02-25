# -*- coding: utf-8 -*-

import os
import json
import logging

from tornado import web
from tornado import gen

from litepipeline.node.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.node.utils.executor import Executor
from litepipeline.node.utils.common import Errors
from litepipeline.node.config import CONFIG

LOG = logging.getLogger("__name__")


class DeleteTaskWorkspaceHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_infos = self.get_json_argument("task_infos", [])
            failed_task_ids = yield Executor.instance().delete_task_workspace(task_infos)
            result["failed_task_ids"] = failed_task_ids
            LOG.info("DeleteTaskWorkspaceHandler, failed_task_ids: %s, task_infos: %s, data: %s", failed_task_ids, task_infos, self.json_data)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
