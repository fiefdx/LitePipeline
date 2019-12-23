# -*- coding: utf-8 -*-

import os
import time
import json
import logging

from tornado import ioloop
from tornado import gen

from config import CONFIG

LOG = logging.getLogger(__name__)

class Servers(object):
    HTTP_SERVER = None
    DB_SERVERS = []
    TORNADO_INSTANCE = None

async def shutdown():
    LOG.info("Stopping Service(%s:%s)", CONFIG["http_host"], CONFIG["http_port"])
    if Servers.HTTP_SERVER:
        Servers.HTTP_SERVER.stop()
        LOG.info("Stop http server!")
    for db_server in Servers.DB_SERVERS:
        db_server.close()
        LOG.info("Stop db server!")
    await gen.sleep(1)
    LOG.info("Will shutdown ...")
    ioloop.IOLoop.current().stop()

def sig_handler(sig, frame):
    LOG.warning("sig_handler Caught signal: %s", sig)
    ioloop.IOLoop.current().add_callback_from_signal(shutdown)

class Errors(object):
    OK = "ok"
    errors = {
        "ServerException": {"name": "ServerException", "message": "server exception"},
        "InvalidParameters": {"name": "InvalidParameters", "message": "invalid parameters"},
        "SameNameFileExists": {"name": "SameNameFileExists", "message": "same name file or directory exists"},
        "TargetDirNotExists": {"name": "TargetDirNotExists", "message": "target directory do not exists"},
        "FileOrDirNotExists": {"name": "FileOrDirNotExists", "message": "file or directory do not exists"},
        "TargetTypeNotDir": {"name": "TargetTypeNotDir", "message": "target is not a directory"},
    }

    @classmethod
    def set_result_error(cls, error_name, result, message = ""):
        if error_name in cls.errors:
            result["result"] = error_name
            if message == "":
                result["message"] = cls.errors[error_name]["message"]
            else:
                result["message"] = message
        else:
            result["result"] = "UnknownError"
            result["message"] = "unknown error"

class JSONLoadError(Exception):
    def __init__(self, message):
        self.message = message

class MetaNotDictError(Exception):
    def __init__(self, message):
        self.message = message
