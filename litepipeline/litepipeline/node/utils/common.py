# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import hashlib
import logging
import datetime
import configparser
import threading
from threading import Thread, Lock
import zipfile
from zipfile import ZipFile, ZipInfo
from uuid import UUID

from tornado import ioloop
from tornado import gen

from litepipeline.node.config import CONFIG

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


def has_parent_directory(parent, paths):
    result = True
    for p in paths:
        if not p.startswith(parent):
            result = False
            break
    return result


def get_workspace_path(create_at, task_id = None, action_name = None, service_id = None, config = None):
    result = ""
    date_create_at = datetime.datetime.strptime(create_at, "%Y-%m-%d %H:%M:%S.%f")
    date_directory_name = date_create_at.strftime("%Y-%m-%d")
    data_path = CONFIG["data_path"] if config is None else config["data_path"]
    if service_id:
        result = os.path.join(data_path, "tmp", "service_workspace", service_id[:2], service_id[2:4], service_id, action_name)
    elif task_id and action_name:
        result = os.path.join(data_path, "tmp", "workspace", date_directory_name, task_id[:2], task_id[2:4], task_id, action_name)
    elif task_id:
        result = os.path.join(data_path, "tmp", "workspace", date_directory_name, task_id[:2], task_id[2:4], task_id)
    else:
        result = os.path.join(data_path, "tmp", "workspace", date_directory_name)
    return result


def get_download_path(task_id, action_name, service_id, config = None):
    result = ""
    data_path = CONFIG["data_path"] if config is None else config["data_path"]
    if service_id and action_name:
        result = os.path.join(data_path, "tmp", "download", "%s.%s.tar.gz" % (service_id, action_name))
    elif task_id and action_name:
        result = os.path.join(data_path, "tmp", "download", "%s.%s.tar.gz" % (task_id, action_name))
    else:
        result = os.path.join(data_path, "tmp", "download")
    return result


class FakeSectionHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[global]\n'

    def readline(self):
        if self.sechead:
            try: 
                return self.sechead
            finally: 
                self.sechead = None
        else: 
            return self.fp.readline()

    def __iter__(self):
        line = self.readline()
        while line:
            yield line
            line = self.readline()

    def close(self):
        self.fp.close()


def update_venv_cfg(venv_path):
    venv_path = venv_path
    cfg_path = os.path.join(venv_path, "pyvenv.cfg")
    config = configparser.ConfigParser()
    items = []
    if os.path.exists(cfg_path) and os.path.isfile(cfg_path):
        fp = FakeSectionHead(open(cfg_path))
        config.read_file(fp)
        fp.close()
        items = config.items("global")
        LOG.debug(items)
        with open(cfg_path, "w") as fp:
            for item in items:
                if item[0] == "home":
                    python_home_path = item[1]
                    if sys.base_prefix:
                        python_home_path = os.path.join(sys.base_prefix, "bin")
                    elif sys.base_exec_prefix:
                        python_home_path = os.path.join(sys.base_exec_prefix, "bin")
                    fp.write("%s = %s\n" % ("home", python_home_path))
                else:
                    fp.write("%s = %s\n" % item)


class StoppableThread(Thread):
    """
    Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition.
    """

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.isSet()


class ZipFileWithPermissions(ZipFile):
    '''
    Custom ZipFile class handling file permissions
    '''

    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        targetpath = super()._extract_member(member, targetpath, pwd)

        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(targetpath, attr)
        return targetpath


def is_uuid(u, version = 4):
    result = True
    try:
        UUID(u, version = version)
    except Exception as e:
        result = False
    return result


def init_storage():
    directories = [
        os.path.join(CONFIG["data_path"], "venvs"),
        os.path.join(CONFIG["data_path"], "applications"),
        os.path.join(CONFIG["data_path"], "tmp", "service_workspace"),
        os.path.join(CONFIG["data_path"], "tmp", "workspace"),
        os.path.join(CONFIG["data_path"], "tmp", "download"),
    ]
    for d in directories:
        if not os.path.exists(d) or not os.path.isdir(d):
            os.makedirs(d)
