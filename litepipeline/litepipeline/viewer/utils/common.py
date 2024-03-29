# -*- coding: utf-8 -*-

import os
import time
import json
import hashlib
import logging
import datetime
from base64 import b64decode, b64encode

from tornado import ioloop
from tornado import gen
from tea_encrypt import EncryptStr, DecryptStr

from litepipeline.viewer.config import CONFIG

LOG = logging.getLogger(__name__)

BUF_SIZE = 65536


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
        "OperationFailed": {"name": "OperationFailed", "message": "operation failed"},
        "AppNotExists": {"name": "AppNotExists", "message": "application not exists"},
        "TaskNotExists": {"name": "TaskNotExists", "message": "task not exists"},
        "OperationRunning": {"name": "OperationRunning", "message": "operation running"},
        "WorkspaceNotExists": {"name": "WorkspaceNotExists", "message": "workspace not exists"},
        "WorkspaceNotPacked": {"name": "WorkspaceNotPacked", "message": "workspace not packed"},
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


class Stage(object):
    pending = "pending"
    running = "running"
    finished = "finished"


class Status(object):
    fail = "fail"
    success = "success"
    kill = "kill"
    cancel = "cancel"
    terminate = "terminate"


class Signal(object):
    kill = -9
    terminate = -15
    stop = -15
    cancel = -50


class JSONLoadError(Exception):
    def __init__(self, message):
        self.message = message


class MetaNotDictError(Exception):
    def __init__(self, message):
        self.message = message


def file_sha1sum(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def file_md5sum(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as fp:
        while True:
            data = fp.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def bytes_md5sum(b):
    md5 = hashlib.md5()
    md5.update(b)
    return md5.hexdigest()


def encode_token(user, password):
    return b64encode(EncryptStr(user.encode("utf-8"),
                                bytes_md5sum(password.encode("utf-8"))
    ))


def splitall(path):
    allparts = []
    while True:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def get_workspace_path(create_at, task_id = None, action_name = None):
    result = ""
    date_create_at = datetime.datetime.strptime(create_at, "%Y-%m-%d %H:%M:%S.%f")
    date_directory_name = date_create_at.strftime("%Y-%m-%d")
    if task_id and action_name:
        result = os.path.join(CONFIG["data_path"], "tmp", "workspace", date_directory_name, task_id[:2], task_id[2:4], task_id, action_name)
    elif task_id:
        result = os.path.join(CONFIG["data_path"], "tmp", "workspace", date_directory_name, task_id[:2], task_id[2:4], task_id)
    else:
        result = os.path.join(CONFIG["data_path"], "tmp", "workspace", date_directory_name)
    return result


def init_storage():
    directories = [
        os.path.join(CONFIG["data_path"], "applications"),
        os.path.join(CONFIG["data_path"], "tmp", "workspace"),
        os.path.join(CONFIG["data_path"], "tmp", "download"),
    ]
    for d in directories:
        if not os.path.exists(d) or not os.path.isdir(d):
            os.makedirs(d)
