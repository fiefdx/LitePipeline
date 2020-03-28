# -*- coding: utf-8 -*-

import json
import time
import urllib
import logging

from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.manager.models.workflows import Workflows
from litepipeline.manager.models.works import Works
from litepipeline.manager.utils.scheduler import Scheduler
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, Stage, Status, Signal, splitall, JSONLoadError
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class CreateWorkHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            name = self.get_json_argument("name", "")
            workflow_id = self.get_json_argument("workflow_id", "")
            input_data = self.get_json_argument("input_data", {})
            workflow = Workflows.instance().get(workflow_id)
            if workflow and name:
                if not isinstance(input_data, dict):
                    raise JSONLoadError("input_data must be dict type")
                work_id = Works.instance().add(name, workflow_id, input_data = input_data, configuration = workflow["configuration"])
                if work_id is not False:
                    result["work_id"] = work_id
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("CreateWorkHandler, name: %s, workflow_id: %s", name, workflow_id)
        except JSONLoadError as e:
            LOG.error(e)
            Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class RunWorkHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            pass
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class RecoverWorkHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            pass
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class StopWorkHandler(BaseHandler): # kill -9 or -15
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            pass
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteWorkHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            work_id = self.get_argument("work_id", "")
            if work_id:
                success = Works.instance().delete(work_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class InfoWorkHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            work_id = self.get_argument("work_id", "")
            if work_id:
                work_info = Works.instance().get(work_id)
                if work_info:
                    result["info"] = work_info
                elif work_info is None:
                    Errors.set_result_error("WorkNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class ListWorkHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            stage = self.get_argument("stage", "")
            LOG.debug("ListWorkHandler offset: %s, limit: %s, stage: %s", offset, limit, stage)
            r = Works.instance().list(offset = offset, limit = limit, stage = stage)
            result["works"] = r["works"]
            result["total"] = r["total"]
            result["offset"] = offset
            result["limit"] = limit
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class CleanWorkHistoryHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()
