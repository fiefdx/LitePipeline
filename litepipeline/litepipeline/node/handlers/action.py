# -*- coding: utf-8 -*-

import os
import io
import re
import json
import time
import logging
import tarfile

import requests
from tornado import web
from tornado import gen
from tornado import httpclient

from litepipeline.node.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.node.utils.executor import Executor
from litepipeline.node.utils.common import Errors, Signal, file_sha1sum, get_workspace_path
from litepipeline.node.config import CONFIG

LOG = logging.getLogger("__name__")


class RunActionHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            app_id = self.get_json_argument("app_id", "")
            if task_id and app_id:
                Executor.instance().push_action_with_counter(self.json_data)
            else:
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("RunActionHandler, task_id: %s, app_id: %s, data: %s", task_id, app_id, self.json_data)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class StopActionHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            name = self.get_json_argument("name", "")
            signal = int(self.get_json_argument("signal", Signal.kill))
            if task_id and name and signal in (Signal.kill, Signal.terminate):
                success = Executor.instance().stop_action(task_id, name, signal)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
            else:
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("StopActionHandler, task_id: %s, data: %s", task_id, self.json_data)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class CancelActionHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            name = self.get_json_argument("name", "")
            if task_id and name:
                success = Executor.instance().stop_action(task_id, name, Signal.cancel)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
            else:
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("CancelActionHandler, task_id: %s, data: %s", task_id, self.json_data)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class FullStatusHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK, "full": True}
        try:
            full = Executor.instance().is_full()
            result["full"] = full
            LOG.debug("FullStatusHandler, full: %s", full)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class PackWorkspaceHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            task_id = self.get_json_argument("task_id", "")
            create_at = self.get_json_argument("create_at", "")
            name = self.get_json_argument("name", "")
            force = self.get_json_argument("force", False)
            if task_id and create_at and name:
                ready = yield Executor.instance().pack_action_workspace(task_id, create_at, name, force)
                if not ready:
                    Errors.set_result_error("OperationRunning", result)
            else:
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("PackWorkspaceHandler, task_id: %s, create_at: %s, name: %s, data: %s", task_id, create_at, name, self.json_data)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DownloadWorkspaceHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            task_id = self.get_argument("task_id", "")
            create_at = self.get_argument("create_at", "")
            name = self.get_argument("name", "")
            if task_id and create_at and name:
                workspace = get_workspace_path(create_at, task_id, name)
                tar_workspace = os.path.join(CONFIG["data_path"], "tmp", "download", "%s.%s.tar.gz" % (task_id, name))
                if os.path.exists(tar_workspace) and os.path.isfile(tar_workspace):
                    buf_size = 64 * 1024
                    self.set_header('Content-Type', 'application/octet-stream')
                    self.set_header('Content-Disposition', 'attachment; filename=%s.%s.tar.gz' % (task_id, name))
                    with open(tar_workspace, 'rb') as f:
                        while True:
                            data = f.read(buf_size)
                            if not data:
                                break
                            self.write(data)
                            self.flush()
                            yield gen.moment
                    self.finish()
                    return
                elif os.path.exists(workspace) and os.path.isdir(workspace):
                    Errors.set_result_error("WorkspaceNotPacked", result)
                else:
                    Errors.set_result_error("WorkspaceNotExists", result)
            else:
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("DownloadWorkspaceHandler")
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
