# -*- coding: utf-8 -*-

import os
import json
import logging
import tarfile
import shutil
import datetime
import subprocess
from pathlib import Path

import tornado.ioloop
import tornado.web
import requests

from utils.common import Errors, file_sha1sum, splitall
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


class Executor(object):
    def __init__(self, interval = 1):
        self.interval = interval
        self.ioloop_service()
        self.running_actions = []

    def ioloop_service(self):
        self.periodic_execute = tornado.ioloop.PeriodicCallback(
            self.execute_service, 
            self.interval * 1000
        )
        self.periodic_execute.start()

    def push_action(self, action):
        self.running_actions.append(action)

    def pop_action(self):
        result = None
        try:
            result = self.running_actions.pop(0)
        except IndexError:
            LOG.debug("no more action to execute")
        return result

    def update_application(self, app_id):
        url = "http://%s:%s/app/download?app_id=%s" % (CONFIG["manager_http_host"], CONFIG["manager_http_port"], app_id)
        file_path = os.path.join(CONFIG["data_path"], "tmp", "%s.tar.gz" % app_id)
        LOG.debug("download: %s", url)
        r = requests.get(url)
        if r.status_code == 200:
            LOG.debug("download status: %s", r.status_code)
            f = open(file_path, 'wb')
            f.write(r.content)
            f.close()
            app_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
            if os.path.exists(app_path):
                shutil.rmtree(app_path)
            os.makedirs(app_path)
            shutil.copy2(file_path, os.path.join(app_path, "app.tar.gz"))
            os.remove(file_path)
            if os.path.exists(os.path.join(app_path, "app")):
                shutil.rmtree(os.path.join(app_path, "app"))
            t = tarfile.open(os.path.join(app_path, "app.tar.gz"), "r")
            t.extractall(app_path)
            tar_root_name = splitall(t.getnames()[0])[0]
            os.rename(os.path.join(app_path, tar_root_name), os.path.join(app_path, "app"))

    def execute_service(self):
        LOG.debug("execute_service")
        try:
            action = self.pop_action()
            if action:
                name = action["name"]
                task_id = action["task_id"]
                app_id = action["app_id"]
                sha1 = action["app_sha1"]
                if "process" not in action:
                    LOG.debug("execute action: %s", action)
                    app_base_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                    app_tar_path = os.path.join(app_base_path, "app.tar.gz")
                    app_path = os.path.join(app_base_path, "app")
                    if os.path.exists(app_tar_path) and os.path.isfile(app_tar_path):
                        if sha1 != file_sha1sum(app_tar_path):
                            self.update_application(app_id)
                        if not os.path.exists(app_path):
                            self.update_application(app_id)
                    else:
                        self.update_application(app_id)
                    LOG.debug("execute application[%s][%s]", app_path, name)
                    workspace = str(Path(os.path.join(CONFIG["data_path"], "tmp", "workspace", task_id)).resolve())
                    input_data = {"task_id": task_id, "workspace": workspace}
                    if not os.path.exists(workspace):
                        os.makedirs(workspace)
                    fp = open(os.path.join(workspace, "input.data"), "w")
                    fp.write(json.dumps(input_data))
                    fp.close()
                    venv_path = os.path.join(action["env"], "bin", "activate")
                    main_path = action["main"]
                    cmd = "cd %s && source %s && %s %s" % (app_path, venv_path, main_path, workspace)
                    action["process"] = subprocess.Popen(cmd, shell = True, executable = '/bin/bash', bufsize = 0)
                    action["start_at"] = datetime.datetime.now()
                    self.push_action(action)
                else:
                    if action["process"].poll() is None:
                        action["update_at"] = datetime.datetime.now()
                        LOG.debug("action task_id: %s, app_id: %s, name: %s still running", task_id, app_id, name)
                        self.push_action(action)
                    else:
                        returncode = action["process"].poll()
                        LOG.info("action task_id: %s, app_id: %s, name: %s finished: %s", task_id, app_id, name, returncode)
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


ActionExecutor = Executor()
