# -*- coding: utf-8 -*-

import os
import io
import re
import json
import time
import logging

from tornado import web
from tornado import gen

from handlers.base import BaseHandler, BaseSocketHandler
from config import CONFIG

LOG = logging.getLogger("__name__")


@web.stream_request_body
class DeployHandler(BaseHandler):
    PARSE_READY = 0
    PARSE_FILE_PENDING = 1

    def check_xsrf_cookie(self): # ignore xsrf check
        pass

    def prepare(self):
        self.mimetype = self.request.headers.get("Content-Type")
        self.boundary = "--%s" % (self.mimetype[self.mimetype.find("boundary")+9:])
        self.boundary = self.boundary.encode("utf-8")
        self.state = DeployHandler.PARSE_READY
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
                    if self.state == DeployHandler.PARSE_FILE_PENDING:
                        if len(buff) > 1:
                            self.output.write(part[:-2])
                            self.output.close()
                            self.state = DeployHandler.PARSE_READY
                            continue
                        else:
                            self.output.write(part)
                            self.output.flush()
                            continue

                    elif self.state == DeployHandler.PARSE_READY:
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
                                self.state = DeployHandler.PARSE_READY
                            else:
                                self.output.write(body)
                                self.output.flush()
                                self.state = DeployHandler.PARSE_FILE_PENDING
                        else:
                            stream.readline()
                            form_name = re.search(self.find_field, form_data_type_line).groups()[0]
                            form_value = stream.readline()
                            if form_name:
                                self.form_arguments[form_name.strip().decode("utf-8")] = form_value.strip().decode("utf-8")
                            self.state = DeployHandler.PARSE_READY
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
    def get(self):
        result = {"message": "deploy handler"}
        self.write(result)
        self.finish()

    @gen.coroutine
    def post(self):
        try:
            test = self.get_form_argument("test", "default value")
            LOG.debug("get_argument: test = %s", test)
            fp = open(self.file_path, "rb")
            content = fp.read()
            LOG.debug("file content(%s): %s", os.path.exists(self.file_path), content)
            fp.close()
        except Exception as e:
            LOG.exception(e)
        LOG.debug("upload application package use: %ss", time.time() - self.start)
        self.write({"result":"ok"})
        self.finish()
