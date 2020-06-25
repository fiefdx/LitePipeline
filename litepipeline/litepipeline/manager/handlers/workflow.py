# -*- coding: utf-8 -*-

import os
import time
import json
import logging
import shutil
import tarfile

import requests
from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, StreamBaseHandler
from litepipeline.manager.models.workflows import Workflows
from litepipeline.manager.utils.listener import Connection
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, splitall
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class CreateWorkflowHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            name = self.get_json_argument("name", "")
            configuration = self.get_json_argument("configuration", {})
            description = self.get_json_argument("description", "")
            enable = self.get_json_argument("enable", False)
            if name:
                workflow_id = Workflows.instance().add(name, configuration, description = description, enable = enable)
                result["workflow_id"] = workflow_id
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class ListWorkflowHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            filters = {}
            workflow_id = self.get_argument("id", "")
            if workflow_id:
                filters["id"] = workflow_id
            name = self.get_argument("name", "")
            if name:
                filters["name"] = name
            LOG.debug("ListWorkflowHandler offset: %s, limit: %s, filters: %s", offset, limit, filters)
            r = Workflows.instance().list(offset = offset, limit = limit, filters = filters)
            result["workflows"] = r["workflows"]
            result["total"] = r["total"]
            result["offset"] = offset
            result["limit"] = limit
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteWorkflowHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            workflow_id = self.get_argument("workflow_id", "")
            if workflow_id:
                success = Workflows.instance().delete(workflow_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class UpdateWorkflowHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            workflow_id = self.get_json_argument("workflow_id", "")
            name = self.get_json_argument("name", "")
            configuration = self.get_json_argument("configuration", {})
            description = self.get_json_argument("description", "")
            enable = self.get_json_argument("enable", None)
            LOG.debug("UpdateWorkflowHandler workflow_id: %s, name: %s, description: %s", workflow_id, name, description)
            if workflow_id and Workflows.instance().get(workflow_id):
                result["workflow_id"] = workflow_id
                data = {}
                if name:
                    data["name"] = name
                if configuration:
                    data["configuration"] = configuration
                if description:
                    data["description"] = description
                if enable is not None:
                    data["enable"] = enable
                if data:
                    success = Workflows.instance().update(workflow_id, data)
                    if not success:
                        Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class InfoWorkflowHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            workflow_id = self.get_argument("workflow_id", "")
            if workflow_id:
                workflow_info = Workflows.instance().get(workflow_id)
                if workflow_info:
                    result["info"] = workflow_info
                elif workflow_info is None:
                    Errors.set_result_error("AppNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
