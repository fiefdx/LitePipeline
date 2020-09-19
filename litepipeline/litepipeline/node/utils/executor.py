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
import docker

from litepipeline.node.utils.common import Errors, Stage, Status, Signal, file_sha1sum, splitall, get_workspace_path
from litepipeline.node.utils.apps_manager import ManagerClient as AppsManagerClient
from litepipeline.node.utils.workspace_manager import ManagerClient as WorkspaceManagerClient
from litepipeline.node.utils.registrant import Registrant
from litepipeline.node.config import CONFIG
from litepipeline.node import logger

LOG = logging.getLogger(__name__)


class Executor(object):
    _instance = None

    def __new__(cls, config):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.config = config
            cls._instance.interval = config["executor_interval"]
            cls._instance.ioloop_service()
            cls._instance.running_actions = []
            cls._instance.actions_counter = 0
            cls._instance.async_client = AsyncHTTPClient()
            cls._instance.apps_manager = AppsManagerClient()
            cls._instance.workspace_manager = WorkspaceManagerClient()
            cls._instance.docker_client = None
            if CONFIG["docker_support"]:
                cls._instance.docker_client = docker.from_env()
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

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

    @gen.coroutine
    def delete_task_workspace(self, task_infos):
        result = []
        running_task_ids = []
        try:
            for action in self.running_actions:
                running_task_ids.append(action["task_id"])
            for task_info in task_infos:
                task_id = task_info["task_id"]
                create_at = task_info["create_at"]
                if task_id in running_task_ids:
                    result.append(task_id)
                else:
                    workspace = get_workspace_path(create_at, task_id)
                    if os.path.exists(workspace):
                        shutil.rmtree(workspace)
                        LOG.info("delete workspace: %s", workspace)
                        yield gen.moment
        except Exception as e:
            LOG.exception(e)
        return result

    @gen.coroutine
    def pack_action_workspace(self, task_id, create_at, action_name, force = False):
        result = False
        try:
            result = yield self.workspace_manager.pack_workspace(task_id, create_at, action_name, force)
        except Exception as e:
            LOG.exception(e)
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

    def stop_action(self, task_id, action_name, signal):
        result = False
        try:
            for action in self.running_actions:
                if action["task_id"] == task_id and action["name"] == action_name:
                    action["signal"] = signal
                    break
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def update_heartbeat_data(self):
        try:
            data = {"actions_counter": self.actions_counter, "running_actions": []}
            for action in self.running_actions:
                data["running_actions"].append(
                    {
                        "task_id": action["task_id"],
                        "action_name": action["name"],
                        "update_at": str(action["update_at"]) if "update_at" in action else None,
                    }
                )
            Registrant.instance().update_heartbeat_data(data = data)
        except Exception as e:
            LOG.exception(e)

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
                create_at = action["task_create_at"]
                workspace = get_workspace_path(create_at, task_id, name)
                if not os.path.exists(workspace):
                    os.makedirs(workspace)
                workspace = str(Path(workspace).resolve())
                # action not running yet
                if "process" not in action:
                    app_ready = yield self.apps_manager.check_app(app_id)
                    LOG.debug("execute action: %s, app_ready: %s", action, app_ready)
                    if app_ready is True: # start run app ready action
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
                        if CONFIG["docker_support"] and "docker" in action and action["docker"] and "docker_registry" in action and action["docker_registry"]:
                            if "env" in action:
                                venv_path = os.path.join(action["env"], "bin", "activate")
                                cmd = "bash -c \"cd /opt/app && source '%s' && exec %s /opt/workspace --nodaemon\"" % (venv_path, main_path)
                            else:
                                cmd = "bash -c \"cd /opt/app && exec %s /opt/workspace --nodaemon\"" % (main_path, )
                            docker_args = {}
                            if "args" in action["docker"] and action["docker"]["args"]:
                                docker_args = action["docker"]["args"]
                            container = self.docker_client.containers.run(
                                image = "%s/%s:%s" % (action["docker_registry"], action["docker"]["name"], action["docker"]["tag"]),
                                detach = True,
                                volumes = {
                                    app_path: {'bind': '/opt/app', 'mode': 'ro'},
                                    workspace: {'bind': '/opt/workspace', 'mode': 'rw'},
                                },
                                command = cmd,
                                **docker_args,
                            )
                            LOG.debug("docker cmd: %s", cmd)
                            stdout_file_path = os.path.join(workspace, "stdout.data")
                            stdout_file = open(stdout_file_path, "w")
                            action["stdout_file_path"] = stdout_file_path
                            action["stdout_file"] = stdout_file
                            action["process"] = container
                            action["start_at"] = datetime.datetime.now()
                        else:
                            if "env" in action:
                                venv_path = os.path.join(action["env"], "bin", "activate")
                                cmd = "cd %s && source '%s' && exec %s '%s' --nodaemon" % (app_path, venv_path, main_path, workspace)
                            else:
                                cmd = "cd %s && exec %s '%s' --nodaemon" % (app_path, main_path, workspace)
                            LOG.debug("cmd: %s", cmd)
                            stdout_file_path = os.path.join(workspace, "stdout.data")
                            stdout_file = open(stdout_file_path, "w")
                            action["stdout_file_path"] = stdout_file_path
                            action["stdout_file"] = stdout_file
                            action["process"] = subprocess.Popen(cmd, shell = True, executable = '/bin/bash', bufsize = -1, stdout = stdout_file, stderr = subprocess.STDOUT)
                            action["start_at"] = datetime.datetime.now()
                    elif isinstance(app_ready, dict): # stop download app failed action
                        action["process"] = None
                        action["start_at"] = datetime.datetime.now()
                        action["result"] = app_ready
                    else: # stop app not ready action
                        if "signal" in action:
                            action["process"] = None
                            action["start_at"] = datetime.datetime.now()
                    self.push_action(action)
                # action already running
                else:
                    action_stage = Stage.running
                    action_status = Status.success
                    action_result = {}
                    now = datetime.datetime.now()
                    end_at = None
                    returncode = None
                    if action["process"] is None: # stop not running action, not need to push back
                        action["update_at"] = now
                        if "signal" in action:
                            if action["signal"] == Signal.cancel:
                                action["canceled"] = True
                            del action["signal"]
                        if "result" in action:
                            action_result = action["result"]
                            del action["result"]
                        action_stage = Stage.finished
                        end_at = now
                        returncode = 0
                        action_status = Status.fail
                        LOG.info("stop action task_id: %s, app_id: %s, name: %s finished: %s", task_id, app_id, name, returncode)
                    elif isinstance(action["process"], docker.models.containers.Container): # run with docker
                        action["process"].reload()
                        if action["process"].status != "exited": # running action, need to push back
                            action["update_at"] = now
                            if "signal" in action:
                                if action["signal"] == Signal.terminate:
                                    action["process"].kill(-Signal.terminate)
                                elif action["signal"] == Signal.kill:
                                    action["process"].kill(-Signal.kill)
                                elif action["signal"] == Signal.cancel:
                                    action["canceled"] = True
                                    action["process"].kill(-Signal.kill)
                                else:
                                    LOG.warning("unknown signal: %s", action["signal"])
                                del action["signal"]
                            LOG.debug("action task_id: %s, app_id: %s, name: %s still running", task_id, app_id, name)
                            self.push_action(action)
                        else: # finished action, not need to push back
                            action_stage = Stage.finished
                            end_at = now
                            r = action["process"].wait()
                            action["stdout_file"].write(json.dumps(r, indent = 4))
                            returncode = r["StatusCode"]
                            output_data_path = os.path.join(workspace, "output.data")
                            if returncode == 0:
                                if os.path.exists(output_data_path) and os.path.isfile(output_data_path):
                                    fp = open(output_data_path, "r")
                                    action_result = json.loads(fp.read())
                                    fp.close()
                            else:
                                action_status = Status.fail
                            if not action["stdout_file"].closed:
                                action["stdout_file"].close()
                            action["process"].remove()
                            LOG.info("action task_id: %s, app_id: %s, name: %s finished: %s", task_id, app_id, name, returncode)
                    else:
                        if action["process"].poll() is None: # running action, need to push back
                            action["update_at"] = now
                            if "signal" in action:
                                if action["signal"] == Signal.terminate:
                                    action["process"].terminate()
                                elif action["signal"] == Signal.kill:
                                    action["process"].kill()
                                elif action["signal"] == Signal.cancel:
                                    action["canceled"] = True
                                    action["process"].kill()
                                else:
                                    LOG.warning("unknown signal: %s", action["signal"])
                                del action["signal"]
                            LOG.debug("action task_id: %s, app_id: %s, name: %s still running", task_id, app_id, name)
                            self.push_action(action)
                        else: # finished action, not need to push back
                            action_stage = Stage.finished
                            end_at = now
                            returncode = action["process"].poll()
                            output_data_path = os.path.join(workspace, "output.data")
                            if returncode == 0:
                                if os.path.exists(output_data_path) and os.path.isfile(output_data_path):
                                    fp = open(output_data_path, "r")
                                    action_result = json.loads(fp.read())
                                    fp.close()
                            else:
                                action_status = Status.fail
                            if not action["stdout_file"].closed:
                                action["stdout_file"].close()
                            LOG.info("action task_id: %s, app_id: %s, name: %s finished: %s", task_id, app_id, name, returncode)

                    if "canceled" in action and action["canceled"]: # canceled action, not need to update status to manager
                        if action_stage == Stage.finished:
                            self.actions_counter -= 1
                            LOG.debug("remove canceled action: %s, actions_counter: %s", action, self.actions_counter)
                    else: # update action status to manager
                        url = "http://%s:%s/action/update" % (CONFIG["manager_http_host"], CONFIG["manager_http_port"])
                        data = {
                            "name": name,
                            "task_id": task_id,
                            "result": action_result,
                            "stage": action_stage,
                            "status": action_status,
                            "node_id": Registrant.instance().config.get("node_id"),
                            "start_at": str(action["start_at"]),
                            "end_at": str(end_at),
                            "returncode": returncode,
                        }
                        LOG.debug("request: %s", url)
                        request = HTTPRequest(url = url, method = "PUT", body = json.dumps(data))
                        r = yield self.async_client.fetch(request)
                        if r.code != 200 or json.loads(r.body.decode("utf-8"))["result"] != Errors.OK: # update status failed
                            if action_stage == Stage.finished:
                                self.push_action(action)
                            LOG.error("update action status failed, task_id: %s, name: %s", task_id, name)
                        else: # update status succeeded
                            if action_stage == Stage.finished:
                                self.actions_counter -= 1
                                LOG.debug("remove action: %s, actions_counter: %s", action, self.actions_counter)
                        LOG.debug("running action: %s", action)
            self.update_heartbeat_data()
            LOG.debug("actions_counter: %s", self.actions_counter)
        except Exception as e:
            LOG.exception(e)

    def close(self):
        try:
            if self.periodic_execute:
                self.periodic_execute.stop()
            LOG.debug("Executor close")
        except Exception as e:
            LOG.exception(e)
