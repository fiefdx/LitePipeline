# -*- coding: utf-8 -*-

import os
import io
import re
import json
import time
import logging
import shutil

import requests
from tornado import web
from tornado import gen

from handlers.base import BaseHandler, BaseSocketHandler
from models.applications import ApplicationsDB
from utils.listener import Connection
from utils.common import file_sha1sum, file_md5sum, Errors
from config import CONFIG

LOG = logging.getLogger("__name__")


@web.stream_request_body
class DeployApplicationHandler(BaseHandler):
    PARSE_READY = 0
    PARSE_FILE_PENDING = 1

    def check_xsrf_cookie(self): # ignore xsrf check
        pass

    def prepare(self):
        self.mimetype = self.request.headers.get("Content-Type")
        self.boundary = "--%s" % (self.mimetype[self.mimetype.find("boundary")+9:])
        self.boundary = self.boundary.encode("utf-8")
        self.state = DeployApplicationHandler.PARSE_READY
        self.output = None
        self.find_filename = re.compile(b'filename="(.*)"')
        self.find_mimetype = re.compile(b'Content-Type: (.*)')
        self.find_field = re.compile(b'name="(.*)"')
        self.start = time.time()
        self.file_name = ""
        self.file_path = ""
        self.form_arguments = {}

    def data_received(self, data):
        LOG.debug("chunk size: %s", len(data))
        try:
            buff = data.split(self.boundary)
            for index, part in enumerate(buff):
                if part:
                    if part == b"--\r\n":
                        break
                    if self.state == DeployApplicationHandler.PARSE_FILE_PENDING:
                        if len(buff) > 1:
                            self.output.write(part[:-2])
                            self.output.close()
                            self.state = DeployApplicationHandler.PARSE_READY
                            continue
                        else:
                            self.output.write(part)
                            self.output.flush()
                            continue

                    elif self.state == DeployApplicationHandler.PARSE_READY:
                        stream = io.BytesIO(part)
                        stream.readline()
                        form_data_type_line = stream.readline()
                        if form_data_type_line.find(b"filename") > -1:
                            filename = re.search(self.find_filename, form_data_type_line).groups()[0]
                            self.file_name = os.path.split(filename)[-1]
                            self.file_path = os.path.join(CONFIG["data_path"].encode("utf-8"), b"tmp", self.file_name)
                            self.output = open(self.file_path, "wb")
                            content_type_line = stream.readline()
                            mimetype = re.search(self.find_mimetype, content_type_line).groups()[0]
                            LOG.debug("%s with %s" % (filename, mimetype.strip()))
                            stream.readline()
                            body = stream.read()
                            if len(buff) > index + 1:
                                self.output.write(body[:-2])
                                self.output.flush()
                                self.state = DeployApplicationHandler.PARSE_READY
                            else:
                                self.output.write(body)
                                self.output.flush()
                                self.state = DeployApplicationHandler.PARSE_FILE_PENDING
                        else:
                            stream.readline()
                            form_name = re.search(self.find_field, form_data_type_line).groups()[0]
                            form_value = stream.readline()
                            if form_name:
                                self.form_arguments[form_name.strip().decode("utf-8")] = form_value.strip().decode("utf-8")
                            self.state = DeployApplicationHandler.PARSE_READY
                            LOG.debug("%s = %s" % (form_name.strip(), form_value.strip()))
        except Exception as e:
            LOG.exception(e)

    def get_form_argument(self, key, default_value):
        result = default_value
        try:
            if key in self.form_arguments:
                result = self.form_arguments[key]
        except Exception as e:
            LOG.exception(e)
        return result

    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            name = self.get_form_argument("name", "")
            description = self.get_form_argument("description", "")
            if name and os.path.exists(self.file_path) and os.path.isfile(self.file_path):
                sha1 = file_sha1sum(self.file_path)
                LOG.debug("sha1: %s, %s", sha1, type(sha1))
                app_id = ApplicationsDB.add(name, description = description)
                app_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                if not os.path.exists(app_path):
                    os.makedirs(app_path)
                shutil.copy2(self.file_path.decode("utf-8"), app_path)
                result["app_id"] = app_id
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)

            # for conn in Connection.clients:
            #     LOG.debug("conn.info: %s", conn.info)
            #     http_host = conn.info["http_host"]
            #     http_port = conn.info["http_port"]
            #     url = "http://%s:%s/deploy" % (http_host, http_port)
            #     files = {'upload_file': (self.file_name, open(self.file_path,'rb'), b"text/plain")}
            #     values = {"test": test}
            #     r = requests.post(url, files = files, data = values)
            #     LOG.debug("r: %s", r)
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
            LOG.debug("ListApplicationHandler offset: %s, limit: %s", offset, limit)
            result["apps"] = ApplicationsDB.list(offset = offset, limit = limit)
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
                success = ApplicationsDB.delete(app_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


@web.stream_request_body
class UpdateApplicationHandler(BaseHandler):
    PARSE_READY = 0
    PARSE_FILE_PENDING = 1

    def check_xsrf_cookie(self): # ignore xsrf check
        pass

    def prepare(self):
        self.mimetype = self.request.headers.get("Content-Type")
        self.boundary = "--%s" % (self.mimetype[self.mimetype.find("boundary")+9:])
        self.boundary = self.boundary.encode("utf-8")
        self.state = UpdateApplicationHandler.PARSE_READY
        self.output = None
        self.find_filename = re.compile(b'filename="(.*)"')
        self.find_mimetype = re.compile(b'Content-Type: (.*)')
        self.find_field = re.compile(b'name="(.*)"')
        self.start = time.time()
        self.file_name = ""
        self.file_path = ""
        self.form_arguments = {}

    def data_received(self, data):
        LOG.debug("chunk size: %s", len(data))
        try:
            buff = data.split(self.boundary)
            for index, part in enumerate(buff):
                if part:
                    if part == b"--\r\n":
                        break
                    if self.state == UpdateApplicationHandler.PARSE_FILE_PENDING:
                        if len(buff) > 1:
                            self.output.write(part[:-2])
                            self.output.close()
                            self.state = UpdateApplicationHandler.PARSE_READY
                            continue
                        else:
                            self.output.write(part)
                            self.output.flush()
                            continue

                    elif self.state == UpdateApplicationHandler.PARSE_READY:
                        stream = io.BytesIO(part)
                        stream.readline()
                        form_data_type_line = stream.readline()
                        if form_data_type_line.find(b"filename") > -1:
                            filename = re.search(self.find_filename, form_data_type_line).groups()[0]
                            self.file_name = os.path.split(filename)[-1]
                            self.file_path = os.path.join(CONFIG["data_path"].encode("utf-8"), b"tmp", self.file_name)
                            self.output = open(self.file_path, "wb")
                            content_type_line = stream.readline()
                            mimetype = re.search(self.find_mimetype, content_type_line).groups()[0]
                            LOG.debug("%s with %s" % (filename, mimetype.strip()))
                            stream.readline()
                            body = stream.read()
                            if len(buff) > index + 1:
                                self.output.write(body[:-2])
                                self.output.flush()
                                self.state = UpdateApplicationHandler.PARSE_READY
                            else:
                                self.output.write(body)
                                self.output.flush()
                                self.state = UpdateApplicationHandler.PARSE_FILE_PENDING
                        else:
                            stream.readline()
                            form_name = re.search(self.find_field, form_data_type_line).groups()[0]
                            form_value = stream.readline()
                            if form_name:
                                self.form_arguments[form_name.strip().decode("utf-8")] = form_value.strip().decode("utf-8")
                            self.state = UpdateApplicationHandler.PARSE_READY
                            LOG.debug("%s = %s" % (form_name.strip(), form_value.strip()))
        except Exception as e:
            LOG.exception(e)

    def get_form_argument(self, key, default_value):
        result = default_value
        try:
            if key in self.form_arguments:
                result = self.form_arguments[key]
        except Exception as e:
            LOG.exception(e)
        return result

    @gen.coroutine
    def put(self):
        result = {"result": Errors.OK}
        try:
            app_id = self.get_form_argument("app_id", "")
            name = self.get_form_argument("name", "")
            description = self.get_form_argument("description", "")
            LOG.debug("UpdateApplicationHandler app_id: %s, name: %s, description: %s", app_id, name, description)
            if app_id and ApplicationsDB.get(app_id):
                data = {}
                need_update = False
                if name:
                    data["name"] = name
                if description:
                    data["description"] = description
                if os.path.exists(self.file_path) and os.path.isfile(self.file_path):
                    sha1 = file_sha1sum(self.file_path)
                    LOG.debug("sha1: %s, %s", sha1, type(sha1))
                    app_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                    if not os.path.exists(app_path):
                        os.makedirs(app_path)
                    shutil.copy2(self.file_path.decode("utf-8"), app_path)
                    result["app_id"] = app_id
                    need_update = True
                if data or need_update:
                    success = ApplicationsDB.update(app_id, data)
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
                app_info = ApplicationsDB.get(app_id)
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
