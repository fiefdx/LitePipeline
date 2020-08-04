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
from litepipeline.manager.utils.app_manager import AppManager
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, splitall
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class CreateApplicationHandler(StreamBaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            name = self.get_form_argument("name", "")
            description = self.get_form_argument("description", "")
            file_path = self.file_path.decode("utf-8")
            if name and os.path.exists(file_path) and os.path.isfile(file_path):
                file_name = os.path.split(file_path)[-1].lower()
                if ((CONFIG["app_store"].endswith("tar.gz") and file_name.endswith("tar.gz")) or
                    (CONFIG["app_store"].endswith("zip") and file_name.endswith("zip"))):
                    result["app_id"] = AppManager.instance().create(name, description, file_path)
                else:
                    LOG.warning("application wrong format")
                    Errors.set_result_error("AppWrongFormat", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        LOG.debug("deploy application package use: %ss", time.time() - self.start)
        self.write(result)
        self.finish()


class ListApplicationHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            filters = {}
            name = self.get_argument("name", "")
            if name:
                filters["name"] = name
            app_id = self.get_argument("id", "")
            if app_id:
                filters["id"] = app_id
            LOG.debug("ListApplicationHandler offset: %s, limit: %s", offset, limit)
            r = AppManager.instance().list(offset, limit, filters = filters)
            result["apps"] = r["apps"]
            result["total"] = r["total"]
            result["offset"] = offset
            result["limit"] = limit
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteApplicationHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            app_id = self.get_argument("app_id", "")
            if app_id:
                success = AppManager.instance().delete(app_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class UpdateApplicationHandler(StreamBaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            app_id = self.get_form_argument("app_id", "")
            name = self.get_form_argument("name", "")
            description = self.get_form_argument("description", "")
            LOG.debug("UpdateApplicationHandler app_id: %s, name: %s, description: %s", app_id, name, description)
            if app_id and AppManager.instance().info(app_id):
                success = AppManager.instance().update(app_id, name, description, self.file_path.decode("utf-8"))
                if not success:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        LOG.debug("update application package use: %ss", time.time() - self.start)
        self.write(result)
        self.finish()


class InfoApplicationHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            app_id = self.get_argument("app_id", "")
            config = self.get_argument("config", "false")
            config = True if config.lower() == "true" else False
            if app_id:
                app_info = AppManager.instance().info(app_id)
                if app_info:
                    if config:
                        app_config = AppManager.instance().get_app_config(app_id, app_info["sha1"])
                        if app_config:
                            result["app_info"] = app_info
                            result["app_config"] = app_config
                        else:
                            Errors.set_result_error("OperationFailed", result)
                    else:
                        result["app_info"] = app_info
                elif app_info is None:
                    Errors.set_result_error("AppNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DownloadApplicationHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            app_id = self.get_argument("app_id", "")
            sha1 = self.get_argument("sha1", "")
            if app_id:
                app_info = AppManager.instance().info(app_id)
                if app_info:
                    if sha1 == "":
                        sha1 = app_info["sha1"]
                    f = AppManager.instance().open(app_id, sha1)
                    if f:
                        self.set_header('Content-Type', 'application/octet-stream')
                        if "app_store" in CONFIG:
                            if "tar.gz" in CONFIG["app_store"]:
                                self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % app_id)
                            elif "zip" in CONFIG["app_store"]:
                                self.set_header('Content-Disposition', 'attachment; filename=%s.zip' % app_id)
                            else:
                                self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % app_id)
                        else:
                            self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % app_id)
                        buf_size = 1024 * 1024
                        while True:
                            data = f.read(buf_size)
                            if not data:
                                break
                            self.write(data)
                            self.flush()
                            yield gen.moment
                        f.close()
                        self.finish()
                        return
                    else:
                        Errors.set_result_error("OperationFailed", result)
                elif app_info is None:
                    Errors.set_result_error("AppNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.set_status(400)
        self.write(result)
        self.finish()


class ApplicationHistoryListHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK, "app_histories": [], "total": 0}
        try:
            app_id = self.get_argument("app_id", "")
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            if app_id:
                app_info = AppManager.instance().info(app_id)
                if app_info:
                    app_histories = AppManager.instance().list_history(offset, limit, {"app_id": app_id})
                    if app_histories:
                        result["app_histories"] = app_histories["histories"]
                        result["total"] = app_histories["total"]
                    result["offset"] = offset
                    result["limit"] = limit
                elif app_info is None:
                    Errors.set_result_error("AppNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class ApplicationHistoryInfoHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            app_id = self.get_argument("app_id", "")
            history_id = int(self.get_argument("history_id", "-1"))
            config = self.get_argument("config", "false")
            config = True if config.lower() == "true" else False
            if history_id != -1:
                app_history = AppManager.instance().info_history(history_id, app_id)
                if app_history:
                    if config:
                        app_config = AppManager.instance().get_app_config(app_id, app_history["sha1"])
                        if app_config:
                            result["history_info"] = app_history
                            result["history_config"] = app_config
                        else:
                            Errors.set_result_error("OperationFailed", result)
                    else:
                        result["history_info"] = app_history
                elif app_history is None:
                    Errors.set_result_error("AppHistoryNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class ApplicationHistoryActivateHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            history_id = self.get_json_argument("history_id", "")
            app_id = self.get_json_argument("app_id", "")
            if history_id and app_id:
                success = AppManager.instance().activate_history(history_id, app_id = app_id)
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


class ApplicationHistoryDeleteHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            app_id = self.get_argument("app_id", "")
            history_id = int(self.get_argument("history_id", "-1"))
            if history_id != -1 and app_id:
                success = AppManager.instance().delete_history(history_id, app_id)
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