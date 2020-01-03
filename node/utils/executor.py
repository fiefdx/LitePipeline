# -*- coding: utf-8 -*-

import os
import json
import logging
import tarfile
import shutil
import datetime
import subprocess
from pathlib import Path

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.ioloop
import tornado.web
from tornado import gen

from utils.common import Errors, Stage, Status, file_sha1sum, splitall
from utils.apps_manager import ManagerClient
from utils.registrant import NodeRegistrant
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


class Executor(object):
    def __init__(self, interval = 1):
        self.interval = interval
        self.ioloop_service()
        self.running_actions = []
        self.actions_counter = 0
        self.async_client = AsyncHTTPClient()
        self.apps_manager = ManagerClient()

    def ioloop_service(self):
        self.periodic_execute = tornado.ioloop.PeriodicCallback(
            self.execute_service, 
            self.interval * 1000
        )
        self.periodic_execute.start()

    def push_action_with_counter(self, action):
        self.running_actions.append(action)
        self.actions_counter += 1

    def push_action(self, action):
        self.running_actions.append(action)

    def pop_action(self):
        result = None
        try:
            result = self.running_actions.pop(0)
        except IndexError:
            LOG.debug("no more action to execute")
        return result

    def is_full(self):
        result = True
        try:
            LOG.debug("is_full, actions_counter: %s", self.actions_counter)
            result = self.actions_counter >= CONFIG["action_slots"]
        except Exception as e:
            LOG.exception(e)
        return result

    def current_running_actions(self):
        result = []
        try:
            result = self.running_actions
        except Exception as e:
            LOG.exception(e)
        return result

    @gen.coroutine
    def execute_service(self):
        LOG.debug("execute_service")
        try:
            action = self.pop_action()
            if action:
                name = action["name"]
                task_id = action["task_id"]
                app_id = action["app_id"]
                sha1 = action["app_sha1"]
                workspace = os.path.join(CONFIG["data_path"], "tmp", "workspace", task_id, name)
                if not os.path.exists(workspace):
                    os.makedirs(workspace)
                workspace = str(Path(workspace).resolve())
                # action not running yet
                if "process" not in action:
                    app_ready = yield self.apps_manager.check_app(app_id, sha1)
                    LOG.debug("execute action: %s, app_ready: %s", action, app_ready)
                    if app_ready:
                        app_base_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                        app_path = os.path.join(app_base_path, "app")
                        app_path = str(Path(app_path).resolve())
                        LOG.debug("execute application[%s][%s]", app_path, name)
                        input_data = {"task_id": task_id, "workspace": workspace}
                        if "input_data" in action:
                            input_data.update(action["input_data"])
                        if not os.path.exists(workspace):
                            os.makedirs(workspace)
                        fp = open(os.path.join(workspace, "input.data"), "w")
                        fp.write(json.dumps(input_data))
                        fp.close()
                        main_path = action["main"]
                        if "env" in action:
                            venv_path = os.path.join(action["env"], "bin", "activate")
                            cmd = "cd %s && source %s && %s %s" % (app_path, venv_path, main_path, workspace)
                        else:
                            cmd = "cd %s && %s %s" % (app_path, main_path, workspace)
                        LOG.debug("cmd: %s", cmd)
                        action["process"] = subprocess.Popen(cmd, shell = True, executable = '/bin/bash', bufsize = 0)
                        action["start_at"] = datetime.datetime.now()
                    self.push_action(action)
                # action already running
                else:
                    action_stage = Stage.running
                    action_status = Status.success
                    action_result = {}
                    now = datetime.datetime.now()
                    end_at = None
                    if action["process"].poll() is None:
                        action["update_at"] = now
                        LOG.debug("action task_id: %s, app_id: %s, name: %s still running", task_id, app_id, name)
                        self.push_action(action)
                    else:
                        action_stage = Stage.finished
                        end_at = now
                        returncode = action["process"].poll()
                        if returncode == 0:
                            fp = open(os.path.join(workspace, "output.data"), "r")
                            action_result = json.loads(fp.read())
                            fp.close()
                        else:
                            action_status = Status.fail
                        LOG.info("action task_id: %s, app_id: %s, name: %s finished: %s", task_id, app_id, name, returncode)

                    url = "http://%s:%s/action/update" % (CONFIG["manager_http_host"], CONFIG["manager_http_port"])
                    data = {
                        "name": name,
                        "task_id": task_id,
                        "result": action_result,
                        "stage": action_stage,
                        "status": action_status,
                        "node_id": NodeRegistrant.config.get("node_id"),
                        "start_at": str(action["start_at"]),
                        "end_at": str(end_at),
                    }
                    LOG.debug("request: %s", url)
                    request = HTTPRequest(url = url, method = "PUT", body = json.dumps(data))
                    r = yield self.async_client.fetch(request)
                    if r.code != 200 or json.loads(r.body.decode("utf-8"))["result"] != Errors.OK:
                        if action_stage == Stage.finished:
                            self.push_action(action)
                        LOG.error("update action status failed, task_id: %s, name: %s", task_id, name)
                    else:
                        if action_stage == Stage.finished:
                            self.actions_counter -= 1
                            LOG.debug("remove action: %s, actions_counter: %s", action, self.actions_counter)
                    LOG.debug("running action: %s", action)
        except Exception as e:
            LOG.exception(e)

    def close(self):
        try:
            if self.periodic_execute:
                self.periodic_execute.stop()
            LOG.debug("Executor close")
        except Exception as e:
            LOG.exception(e)


ActionExecutor = Executor(CONFIG["executor_interval"])