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

from litepipeline.manager.handlers.base import BaseHandler, StreamBaseHandler, auth_check
from litepipeline.manager.utils.venv_manager import VenvManager
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, splitall
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class CreateVenvHandler(StreamBaseHandler):
    @auth_check
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            name = self.get_form_argument("name", "")
            description = self.get_form_argument("description", "")
            file_path = self.file_path.decode("utf-8")
            if name and os.path.exists(file_path) and os.path.isfile(file_path):
                file_name = os.path.split(file_path)[-1].lower()
                if ((CONFIG["venv_store"].endswith("tar.gz") and file_name.endswith("tar.gz")) or
                    (CONFIG["venv_store"].endswith("zip") and file_name.endswith("zip"))):
                    result["venv_id"] = VenvManager.instance().create(name, description, file_path)
                else:
                    LOG.warning("venv wrong format")
                    Errors.set_result_error("VenvWrongFormat", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        LOG.debug("deploy venv package use: %ss", time.time() - self.start)
        self.write(result)
        self.finish()


class ListVenvHandler(BaseHandler):
    @auth_check
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
            venv_id = self.get_argument("id", "")
            if venv_id:
                filters["id"] = venv_id
            LOG.debug("ListVenvHandler offset: %s, limit: %s", offset, limit)
            r = VenvManager.instance().list(offset, limit, filters = filters)
            result["venvs"] = r["venvs"]
            result["total"] = r["total"]
            result["offset"] = offset
            result["limit"] = limit
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteVenvHandler(BaseHandler):
    @auth_check
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            venv_id = self.get_argument("venv_id", "")
            if venv_id:
                success = VenvManager.instance().delete(venv_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class UpdateVenvHandler(StreamBaseHandler):
    @auth_check
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            venv_id = self.get_form_argument("venv_id", "")
            name = self.get_form_argument("name", "")
            description = self.get_form_argument("description", "")
            LOG.debug("UpdateVenvHandler venv_id: %s, name: %s, description: %s", venv_id, name, description)
            if venv_id and VenvManager.instance().info(venv_id):
                success = VenvManager.instance().update(venv_id, name, description, self.file_path.decode("utf-8"))
                if not success:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        LOG.debug("update venv package use: %ss", time.time() - self.start)
        self.write(result)
        self.finish()


class InfoVenvHandler(BaseHandler):
    @auth_check
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            venv_id = self.get_argument("venv_id", "")
            if venv_id:
                venv_info = VenvManager.instance().info(venv_id)
                if venv_info:
                    result["venv_info"] = venv_info
                elif venv_info is None:
                    Errors.set_result_error("VenvNotExists", result)
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


class DownloadVenvHandler(BaseHandler):
    @auth_check
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            venv_id = self.get_argument("venv_id", "")
            sha1 = self.get_argument("sha1", "")
            if venv_id:
                venv_info = VenvManager.instance().info(venv_id)
                if venv_info:
                    if sha1 == "":
                        sha1 = venv_info["sha1"]
                    f = VenvManager.instance().open(venv_id, sha1)
                    if f:
                        self.set_header('Content-Type', 'application/octet-stream')
                        if "venv_store" in CONFIG:
                            if "tar.gz" in CONFIG["venv_store"]:
                                self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % venv_id)
                            elif "zip" in CONFIG["venv_store"]:
                                self.set_header('Content-Disposition', 'attachment; filename=%s.zip' % venv_id)
                            else:
                                self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % venv_id)
                        else:
                            self.set_header('Content-Disposition', 'attachment; filename=%s.tar.gz' % venv_id)
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
                elif venv_info is None:
                    Errors.set_result_error("VenvNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.set_status(400)
        self.write(result)
        self.finish()


class VenvHistoryListHandler(BaseHandler):
    @auth_check
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK, "venv_histories": [], "total": 0}
        try:
            venv_id = self.get_argument("venv_id", "")
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            if venv_id:
                venv_info = VenvManager.instance().info(venv_id)
                if venv_info:
                    venv_histories = VenvManager.instance().list_history(offset, limit, {"venv_id": venv_id})
                    if venv_histories:
                        result["venv_histories"] = venv_histories["histories"]
                        result["total"] = venv_histories["total"]
                    result["offset"] = offset
                    result["limit"] = limit
                elif venv_info is None:
                    Errors.set_result_error("VenvNotExists", result)
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


class VenvHistoryInfoHandler(BaseHandler):
    @auth_check
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            venv_id = self.get_argument("venv_id", "")
            history_id = int(self.get_argument("history_id", "-1"))
            if history_id != -1:
                venv_history = VenvManager.instance().info_history(history_id, venv_id)
                if venv_history:
                    result["history_info"] = venv_history
                elif venv_history is None:
                    Errors.set_result_error("VenvHistoryNotExists", result)
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


class VenvHistoryActivateHandler(BaseHandler):
    @auth_check
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            history_id = self.get_json_argument("history_id", "")
            venv_id = self.get_json_argument("venv_id", "")
            if history_id and venv_id:
                success = VenvManager.instance().activate_history(history_id, venv_id = venv_id)
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


class VenvHistoryDeleteHandler(BaseHandler):
    @auth_check
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            venv_id = self.get_argument("venv_id", "")
            history_id = int(self.get_argument("history_id", "-1"))
            if history_id != -1 and venv_id:
                success = VenvManager.instance().delete_history(history_id, venv_id)
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