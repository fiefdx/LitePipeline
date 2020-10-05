# -*- coding: utf-8 -*-

import json
import time
import urllib
import logging

from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.manager.models.services import Services
from litepipeline.manager.utils.app_manager import AppManager
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, Stage, splitall, JSONLoadError
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class CreateServiceHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            name = self.get_json_argument("name", "")
            app_id = self.get_json_argument("app_id", "")
            description = self.get_json_argument("description", "")
            input_data = self.get_json_argument("input_data", {})
            signal = self.get_json_argument("signal", -9)
            enable = True if self.get_json_argument("enable", False) else False
            if AppManager.instance().info(app_id) and name:
                if not isinstance(input_data, dict):
                    raise JSONLoadError("input_data must be dict type")
                service_id = Services.instance().add(
                    name,
                    app_id,
                    description = description,
                    enable = enable,
                    input_data = input_data,
                    signal = signal
                )
                if service_id is not False:
                    result["service_id"] = service_id
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("CreateServiceHandler, name: %s, app_id: %s, enable: %s", name, app_id, enable)
        except JSONLoadError as e:
            LOG.error(e)
            Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class UpdateServiceHandler(BaseHandler):
    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            service_id = self.get_json_argument("service_id", "")
            result["service_id"] = service_id
            data = self.get_json_exists_arguments(
                [
                    "name",
                    "app_id",
                    "description",
                    "input_data",
                    "signal",
                    "enable",
                ]
            )
            if (
                    data and
                    (service_id and Services.instance().get(service_id)) and
                    (("name" in data and data["name"] != "") or "name" not in data) and
                    ("app_id" not in data or ("app_id" in data and AppManager.instance().info(data["app_id"]))) and
                    ("signal" in data and data["signal"] in (-9, -15)) and
                    (("enable" in data and data["enable"] in [True, False]) or "enable" not in data)
                ):
                if "input_data" in data and not isinstance(data["input_data"], dict):
                    raise JSONLoadError("input_data must be dict type")
                if "app_id" in data:
                    data["application_id"] = data["app_id"]
                    del data["app_id"]
                success = Services.instance().update(service_id, data)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("UpdateServiceHandler, service_id: %s, data: %s", service_id, data)
        except JSONLoadError as e:
            LOG.error(e)
            Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteServiceHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            service_id = self.get_argument("service_id", "")
            if service_id:
                success = Services.instance().delete(service_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class InfoServiceHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            service_id = self.get_argument("service_id", "")
            if service_id:
                service_info = Services.instance().get(service_id)
                if service_info:
                    result["service_info"] = service_info
                    if service_id in Services.instance().cache:
                        result["service_cache_info"] = Services.instance().cache[service_id]
                elif service_info is None:
                    Errors.set_result_error("ServiceNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class ListServiceHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            filters = {}
            service_id = self.get_argument("service_id", "")
            if service_id:
                filters["service_id"] = service_id
            app_id = self.get_argument("app_id", "")
            if app_id:
                filters["app_id"] = app_id
            name = self.get_argument("name", "")
            if name:
                filters["name"] = name
            enable = self.get_argument("enable", "").lower()
            if enable == "true":
                enable = True
            elif enable == "false":
                enable = False
            else:
                enable = ""
            if enable is not "":
                filters["enable"] = enable
            LOG.debug("ListServiceHandler offset: %s, limit: %s, filters: %s", offset, limit, filters)
            r = Services.instance().list(offset = offset, limit = limit, filters = filters)
            result["services"] = r["services"]
            result["total"] = r["total"]
            result["offset"] = offset
            result["limit"] = limit
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
