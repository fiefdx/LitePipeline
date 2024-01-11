# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import shutil
import tarfile
import zipfile
from zipfile import ZipFile, ZipInfo
import signal
from pathlib import Path
import threading
from threading import Thread, Lock
from multiprocessing import Process, Queue, Pipe
import configparser

from tornado import gen, locks
import requests
from litepipeline_helper.models.client import LitePipelineClient, OperationFailedError

from litepipeline.node.utils.common import file_sha1sum, splitall, update_venv_cfg, StoppableThread, ZipFileWithPermissions, is_uuid
from litepipeline.node.config import CONFIG
from litepipeline import logger

LOG = logging.getLogger(__name__)


class Command(object):
    check_app = "check_app"
    exit = "exit"


class TasksCache(object):
    tasks = {}
    tasks_lock = Lock()

    @classmethod
    def set(cls, app_id):
        cls.tasks_lock.acquire()
        if app_id not in cls.tasks:
            cls.tasks[app_id] = False
        cls.tasks_lock.release()

    @classmethod
    def get(cls):
        result = False
        cls.tasks_lock.acquire()
        try:
            for app_id in cls.tasks:
                if not cls.tasks[app_id]:
                    cls.tasks[app_id] = True
                    result = app_id
                    break
        except Exception as e:
            LOG.exception(e)
        cls.tasks_lock.release()
        return result

    @classmethod
    def update(cls, app_id, value):
        cls.tasks_lock.acquire()
        if app_id in cls.tasks:
            cls.tasks[app_id] = value
        cls.tasks_lock.release()

    @classmethod
    def peek(cls, app_id):
        result = None
        cls.tasks_lock.acquire()
        if app_id in cls.tasks:
            result = cls.tasks[app_id]
        cls.tasks_lock.release()
        return result

    @classmethod
    def remove(cls, app_id):
        cls.tasks_lock.acquire()
        del cls.tasks[app_id]
        cls.tasks_lock.release()


class WorkerThread(StoppableThread):
    def __init__(self, pid, config):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid
        self.config = config

    def run(self):
        LOG = logging.getLogger("worker")
        LOG.info("Worker(%03d) start", self.pid)
        try:
            lpl = LitePipelineClient(self.config["manager_http_host"],
                                     self.config["manager_http_port"],
                                     user = self.config["manager_user"],
                                     password = self.config["manager_password"])
            while not self.stopped():
                try:
                    success = True
                    app_id = TasksCache.get()
                    if app_id:
                        LOG.info("downloading app_id: %s", app_id)
                        try:
                            tmp_path = os.path.join(self.config["data_path"], "tmp")
                            r = lpl.application_download(app_id, directory = tmp_path)
                            if r:
                                file_path, file_type = r
                                app_path = os.path.join(self.config["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                                if os.path.exists(app_path):
                                    shutil.rmtree(app_path)
                                os.makedirs(app_path)
                                shutil.copy2(file_path, os.path.join(app_path, "app.%s" % file_type))
                                os.remove(file_path)
                                if os.path.exists(os.path.join(app_path, "app")):
                                    shutil.rmtree(os.path.join(app_path, "app"))
                                if file_type == "tar.gz":
                                    t = tarfile.open(os.path.join(app_path, "app.tar.gz"), "r")
                                    t.extractall(app_path)
                                    path_parts = splitall(t.getnames()[0])
                                    app_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                                    t.close()
                                elif file_type == "zip":
                                    z = ZipFileWithPermissions(os.path.join(app_path, "app.zip"), "r")
                                    z.extractall(app_path)
                                    path_parts = splitall(z.namelist()[0])
                                    app_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                                    z.close()
                                app_config_path = os.path.join(app_path, app_root_name, "configuration.json")
                                f = open(app_config_path, "r")
                                app_config = json.loads(f.read())
                                f.close()
                                venvs = set()
                                for action in app_config["actions"]:
                                    if "env" in action and not is_uuid(action["env"]):
                                        venvs.add(action["env"])
                                for venv in list(venvs):
                                    venv_tar_path = os.path.join(app_path, app_root_name, "%s.tar.gz" % venv)
                                    if os.path.exists(venv_tar_path) and os.path.isfile(venv_tar_path): 
                                        venv_path = os.path.join(app_path, app_root_name, venv)
                                        if os.path.exists(venv_path):
                                            shutil.rmtree(venv_path)
                                        os.makedirs(venv_path)
                                        t = tarfile.open(venv_tar_path, "r")
                                        t.extractall(venv_path)
                                        t.close()
                                        update_venv_cfg(venv_path)
                                    else: # lose venv file
                                        success = False
                                        TasksCache.update(app_id, {"type": "error", "code": r.status_code, "message": "invalid application[%s] format" % app_id, "result": "invalid application[%s] format" % app_id})
                                        LOG.warning("invalid application[%s] format status: %s", app_id, r.status_code)
                                        break
                                os.rename(os.path.join(app_path, app_root_name), os.path.join(app_path, "app"))
                                if success:
                                    TasksCache.remove(app_id)
                        except OperationFailedError as e:
                            TasksCache.update(app_id, {"type": "error", "code": 400, "message": "download application[%s] failed" % app_id, "result": e})
                            LOG.warning("download[%s] message: %s", app_id, e)
                    else:
                        time.sleep(0.5)
                except Exception as e:
                    LOG.exception(e)
        except Exception as e:
            LOG.exception(e)
        LOG.info("Worker(%03d) exit", self.pid)


class Manager(Process):
    def __init__(self, pipe_client, worker_num, config):
        Process.__init__(self)
        self.pipe_client = pipe_client
        self.worker_num = worker_num
        self.config = config

    def run(self):
        logger.config_logging(file_name = "apps_manager.log",
                              log_level = "NOSET",
                              dir_name = self.config["log_path"],
                              when = "D",
                              interval = 1,
                              max_size = 20,
                              backup_count = 5,
                              console = True)
        LOG = logging.getLogger("manager")

        def sig_handler(sig, frame):
            LOG.warning("sig_handler Caught signal: %s", sig)

        LOG.info("Manager start")
        try:
            signal.signal(signal.SIGTERM, sig_handler)
            signal.signal(signal.SIGINT, sig_handler)

            threads = []
            for i in range(self.worker_num):
                t = WorkerThread(i, self.config)
                t.start()
                threads.append(t)

            lpl = LitePipelineClient(self.config["manager_http_host"],
                                     self.config["manager_http_port"],
                                     user = self.config["manager_user"],
                                     password = self.config["manager_password"])

            while True:
                LOG.debug("Manager main loop")
                command, app_id = self.pipe_client.recv()
                if command == Command.check_app:
                    ready = False
                    try:
                        LOG.debug("check app, app_id: %s", app_id)
                        r = lpl.application_info(app_id)
                        if r and "app_info" in r:
                            app_info = r["app_info"]
                            app_base_path = os.path.join(self.config["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                            app_tar_path = os.path.join(app_base_path, "app.tar.gz")
                            app_zip_path = os.path.join(app_base_path, "app.zip")
                            app_path = os.path.join(app_base_path, "app")
                            # check app.tar.gz
                            if os.path.exists(app_tar_path) and os.path.isfile(app_tar_path):
                                if app_info["sha1"] != file_sha1sum(app_tar_path):
                                    # download app.tar.gz && extract app.tar.gz
                                    pass
                                else:
                                    if not os.path.exists(app_path):
                                        # extract app.tar.gz
                                        pass
                                    else:
                                        ready = True
                            # check app.zip
                            if os.path.exists(app_zip_path) and os.path.isfile(app_zip_path):
                                if app_info["sha1"] != file_sha1sum(app_zip_path):
                                    # download app.zip && extract app.zip
                                    pass
                                else:
                                    if not os.path.exists(app_path):
                                        # extract app.tar.gz
                                        pass
                                    else:
                                        ready = True
                            # download app.tar.gz && extract app.tar.gz
                            if ready:
                                status = TasksCache.peek(app_id)
                                if status is not None:
                                    ready = False
                            else:
                                status = TasksCache.peek(app_id)
                                if isinstance(status, dict):
                                    ready = status
                                    TasksCache.remove(app_id)
                                elif status is None:
                                    TasksCache.set(app_id)
                    except Exception as e:
                        LOG.exception(e)
                        ready = {"type": "error", "message": "get app[%s] info failed: %s" % (app_id, str(e))}
                    self.pipe_client.send((command, ready))
                elif command == Command.exit:
                    for t in threads:
                        t.stop()
                    break
            for t in threads:
                t.join()
        except Exception as e:
            LOG.exception(e)
        LOG.info("Manager exit")


class ManagerClient(object):
    process_list = []
    process_dict = {}
    write_lock = locks.Lock()
    _instance = None

    def __init__(self, worker_num = 1):
        if ManagerClient._instance is None:
            self.worker_num = worker_num if worker_num > 0 else 1
            LOG.debug("ManagerClient, worker_num: %s", self.worker_num)
            pipe_master, pipe_client = Pipe()
            p = Manager(pipe_client, self.worker_num, CONFIG)
            p.daemon = True
            ManagerClient.process_list.append(p)
            ManagerClient.process_dict["manager"] = [p, pipe_master]
            p.start()
            ManagerClient._instance = self
        else:
            self.worker_num = ManagerClient._instance.worker_num

    @gen.coroutine
    def check_app(self, app_id):
        result = False
        LOG.debug("start check app, app_id: %s", app_id)
        with (yield ManagerClient.write_lock.acquire()):
            LOG.debug("get check app lock, app_id: %s", app_id)
            ManagerClient.process_dict["manager"][1].send((Command.check_app, app_id))
            LOG.debug("send check app, app_id: %s", app_id)
            while not ManagerClient.process_dict["manager"][1].poll():
                yield gen.moment
            LOG.debug("recv check app, app_id: %s", app_id)
            r = ManagerClient.process_dict["manager"][1].recv()
            LOG.debug("end check app, app_id: %s, r: %s", app_id, r)
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    def close(self):
        try:
            LOG.info("close ManagerClient")
            ManagerClient.process_dict["manager"][1].send((Command.exit, None))
            for p in ManagerClient.process_list[1:]:
                p.terminate()
            for p in ManagerClient.process_list:
                while p.is_alive():
                    time.sleep(0.5)
                    LOG.debug("sleep 0.5 second")
            LOG.info("All Process Exit!")
        except Exception as e:
            LOG.exception(e)
