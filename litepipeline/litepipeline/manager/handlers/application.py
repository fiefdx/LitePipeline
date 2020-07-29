# -*- coding: utf-8 -*-

import os
import time
import logging
import shutil
import tarfile

import requests
from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, StreamBaseHandler
from litepipeline.manager.utils.app_manager import AppLocalTarGzManager
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
            if name and os.path.exists(self.file_path) and os.path.isfile(self.file_path):
                result["app_id"] = AppLocalTarGzManager.instance().create(name, description, self.file_path)
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
            r = AppLocalTarGzManager.instance().list(offset, limit, filters = filters)
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
                success = AppLocalTarGzManager.instance().delete(app_id)
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
            if app_id and AppLocalTarGzManager.instance().info(app_id):
                success = AppLocalTarGzManager.instance().update(app_id, name, description, self.file_path)
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
            if app_id:
                app_info = AppLocalTarGzManager.instance().info(app_id)
                if app_info:
                    result["app_info"] = app_info
                elif app_info is None:
                    Errors.set_result_error("AppNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
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
            if app_id:
                app_info = AppLocalTarGzManager.instance().info(app_id)
                if app_info:
                    f = AppLocalTarGzManager.instance().open(app_id)
                    if f:
                        self.set_header('Content-Type', 'application/octet-stream')
                        self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % app_id)
                        buf_size = 64 * 1024
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
