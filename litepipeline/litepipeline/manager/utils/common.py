# -*- coding: utf-8 -*-

import os
import time
import json
import hashlib
import logging

from litepipeline.manager.config import CONFIG

LOG = logging.getLogger(__name__)

BUF_SIZE = 65536


class Errors(object):
    OK = "ok"
    errors = {
        "ServerException": {"name": "ServerException", "message": "server exception"},
        "InvalidParameters": {"name": "InvalidParameters", "message": "invalid parameters"},
        "OperationFailed": {"name": "OperationFailed", "message": "operation failed"},
        "AppNotExists": {"name": "AppNotExists", "message": "application not exists"},
        "AppWrongFormat": {"name": "AppWrongFormat", "message": "application wrong format"},
        "AppHistoryNotExists": {"name": "AppHistoryNotExists", "message": "application history not exists"},
        "TaskNotExists": {"name": "TaskNotExists", "message": "task not exists"},
        "TaskAlreadyFinished": {"name": "TaskAlreadyFinished", "message": "task already finished"},
        "TaskAlreadySuccess": {"name": "TaskAlreadySuccess", "message": "task already success"},
        "TaskStillRunning": {"name": "TaskStillRunning", "message": "task still running"},
        "WorkNotExists": {"name": "WorkNotExists", "message": "work not exists"},
        "WorkAlreadyFinished": {"name": "WorkAlreadyFinished", "message": "work already finished"},
        "WorkAlreadySuccess": {"name": "WorkAlreadySuccess", "message": "work already success"},
        "WorkStillRunning": {"name": "WorkStillRunning", "message": "work still running"},
        "WorkflowDisabled": {"name": "WorkflowDisabled", "message": "workflow disabled"},
        "WorkflowNotExists": {"name": "WorkflowNotExists", "message": "workflow not exists"},
        "NodeNotExists": {"name": "NodeNotExists", "message": "node not exists"},
        "ActionNotFinished": {"name": "ActionNotFinished", "message": "action not finished"},
        "ActionNoNodeId": {"name": "ActionNoNodeId", "message": "action no node id"},
        "ActionNotRun": {"name": "ActionNotRun", "message": "action not run"},
        "ScheduleNotExists": {"name": "ScheduleNotExists", "message": "schedule not exists"},
        "ServiceNotExists": {"name": "ServiceNotExists", "message": "service not exists"},
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
    stopping = "stopping"
    recovering = "recovering"


class Status(object):
    fail = "fail"
    success = "success"
    kill = "kill"
    cancel = "cancel"
    terminate = "terminate"
    error = "error"


class Signal(object):
    kill = -9
    terminate = -15
    stop = -15
    cancel = -50


class Event(object):
    events = ["fail", "success"]
    fail = "fail"
    success = "success"


class JSONLoadError(Exception):
    def __init__(self, message):
        self.message = message


class MetaNotDictError(Exception):
    def __init__(self, message):
        self.message = message


class OperationError(Exception):
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


def init_storage():
    directories = [
        os.path.join(CONFIG["data_path"], "applications"),
        os.path.join(CONFIG["data_path"], "tmp"),
    ]
    for d in directories:
        if not os.path.exists(d) or not os.path.isdir(d):
            os.makedirs(d)
