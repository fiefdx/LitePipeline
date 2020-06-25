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
from litepipeline.manager.models.applications import Applications
from litepipeline.manager.utils.listener import Connection
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
                sha1 = file_sha1sum(self.file_path)
                LOG.debug("sha1: %s, %s", sha1, type(sha1))
                app_id = Applications.instance().add(name, sha1, description = description)
                app_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                if os.path.exists(app_path):
                    shutil.rmtree(app_path)
                os.makedirs(app_path)
                shutil.copy2(self.file_path.decode("utf-8"), os.path.join(app_path, "app.tar.gz"))
                os.remove(self.file_path)
                if os.path.exists(os.path.join(app_path, "app")):
                    shutil.rmtree(os.path.join(app_path, "app"))
                t = tarfile.open(os.path.join(app_path, "app.tar.gz"), "r")
                t.extractall(app_path)
                path_parts = splitall(t.getnames()[0])
                tar_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                t.close()
                os.rename(os.path.join(app_path, tar_root_name), os.path.join(app_path, "app"))
                result["app_id"] = app_id
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
            r = Applications.instance().list(offset = offset, limit = limit, filters = filters)
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
                success = Applications.instance().delete(app_id)
                if success:
                    app_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                    if os.path.exists(app_path):
                        shutil.rmtree(app_path)
                        LOG.debug("remove directory: %s", app_path) 
                else:
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
            if app_id and Applications.instance().get(app_id):
                data = {}
                need_update = False
                if name:
                    data["name"] = name
                if description:
                    data["description"] = description
                if os.path.exists(self.file_path) and os.path.isfile(self.file_path):
                    sha1 = file_sha1sum(self.file_path)
                    data["sha1"] = sha1
                    LOG.debug("sha1: %s, %s", sha1, type(sha1))
                    app_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                    if os.path.exists(app_path):
                        shutil.rmtree(app_path)
                    os.makedirs(app_path)
                    shutil.copy2(self.file_path.decode("utf-8"), os.path.join(app_path, "app.tar.gz"))
                    os.remove(self.file_path)
                    if os.path.exists(os.path.join(app_path, "app")):
                        shutil.rmtree(os.path.join(app_path, "app"))
                    t = tarfile.open(os.path.join(app_path, "app.tar.gz"), "r")
                    t.extractall(app_path)
                    tar_root_name = splitall(t.getnames()[0])[0]
                    os.rename(os.path.join(app_path, tar_root_name), os.path.join(app_path, "app"))
                    result["app_id"] = app_id
                    need_update = True
                if data or need_update:
                    success = Applications.instance().update(app_id, data)
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
                app_info = Applications.instance().get(app_id)
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
                app_info = Applications.instance().get(app_id)
                if app_info:
                    app_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id, "app.tar.gz")
                    if os.path.exists(app_path):
                        buf_size = 64 * 1024
                        self.set_header('Content-Type', 'application/octet-stream')
                        self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % app_id)
                        with open(app_path, 'rb') as f:
                            while True:
                                data = f.read(buf_size)
                                if not data:
                                    break
                                self.write(data)
                                self.flush()
                                yield gen.moment
                        self.finish()
                        return
                elif app_info is None:
                    Errors.set_result_error("AppNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
