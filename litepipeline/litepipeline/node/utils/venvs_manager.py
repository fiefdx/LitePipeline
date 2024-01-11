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

from tornado import gen, locks
import requests
from litepipeline_helper.models.client import LitePipelineClient

from litepipeline.node.utils.common import file_sha1sum, splitall, update_venv_cfg, StoppableThread, ZipFileWithPermissions, has_parent_directory
from litepipeline.node.config import CONFIG
from litepipeline import logger

LOG = logging.getLogger(__name__)


class Command(object):
    check_venv = "check_venv"
    exit = "exit"


class TasksCache(object):
    tasks = {}
    tasks_lock = Lock()

    @classmethod
    def set(cls, venv_id):
        cls.tasks_lock.acquire()
        if venv_id not in cls.tasks:
            cls.tasks[venv_id] = False
        cls.tasks_lock.release()

    @classmethod
    def get(cls):
        result = False
        cls.tasks_lock.acquire()
        try:
            for venv_id in cls.tasks:
                if not cls.tasks[venv_id]:
                    cls.tasks[venv_id] = True
                    result = venv_id
                    break
        except Exception as e:
            LOG.exception(e)
        cls.tasks_lock.release()
        return result

    @classmethod
    def update(cls, venv_id, value):
        cls.tasks_lock.acquire()
        if venv_id in cls.tasks:
            cls.tasks[venv_id] = value
        cls.tasks_lock.release()

    @classmethod
    def peek(cls, venv_id):
        result = None
        cls.tasks_lock.acquire()
        if venv_id in cls.tasks:
            result = cls.tasks[venv_id]
        cls.tasks_lock.release()
        return result

    @classmethod
    def remove(cls, venv_id):
        cls.tasks_lock.acquire()
        del cls.tasks[venv_id]
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
                    venv_id = TasksCache.get()
                    if venv_id:
                        LOG.info("downloading venv_id: %s", venv_id)
                        try:
                            tmp_path = os.path.join(self.config["data_path"], "tmp")
                            r = lpl.venv_download(venv_id, directory = tmp_path)
                            if r:
                                file_path, file_type = r
                                venv_path = os.path.join(self.config["data_path"], "venvs", venv_id[:2], venv_id[2:4], venv_id)
                                if os.path.exists(venv_path):
                                    shutil.rmtree(venv_path)
                                os.makedirs(venv_path)
                                shutil.copy2(file_path, os.path.join(venv_path, "venv.%s" % file_type))
                                os.remove(file_path)
                                if os.path.exists(os.path.join(venv_path, "venv")):
                                    shutil.rmtree(os.path.join(venv_path, "venv"))
                                if file_type == "tar.gz":
                                    t = tarfile.open(os.path.join(venv_path, "venv.tar.gz"), "r")
                                    sub_paths = t.getnames()
                                    path_parts = splitall(sub_paths[0])
                                    venv_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                                    if has_parent_directory(venv_root_name, sub_paths):
                                        t.extractall(venv_path)
                                        t.close()
                                    else:
                                        t.extractall(os.path.join(venv_path, "venv"))
                                        venv_root_name = "venv"
                                        t.close()
                                elif file_type == "zip":
                                    z = ZipFileWithPermissions(os.path.join(venv_path, "venv.zip"), "r")
                                    sub_paths = z.namelist()
                                    path_parts = splitall(sub_paths[0])
                                    venv_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                                    if has_parent_directory(venv_root_name, sub_paths):
                                        z.extractall(venv_path)
                                        z.close()
                                    else:
                                        z.extractall(os.path.join(venv_path, "venv"))
                                        venv_root_name = "venv"
                                        z.close()
                                if venv_root_name:
                                    os.rename(os.path.join(venv_path, venv_root_name), os.path.join(venv_path, "venv"))
                                    update_venv_cfg(os.path.join(venv_path, "venv"))
                                    TasksCache.remove(venv_id)
                                else:
                                    TasksCache.update(venv_id, {"type": "error", "code": r.status_code, "message": "invalid venv[%s] format" % venv_id, "result": "invalid venv[%s] format" % venv_id})
                                    LOG.warning("invalid venv[%s] format status: %s", venv_id, r.status_code)
                            elif r.status_code == 400:
                                TasksCache.update(venv_id, {"type": "error", "code": r.status_code, "message": "download venv[%s] failed" % venv_id, "result": r.json()})
                                LOG.warning("download[%s] status: %s", venv_id, r.status_code)
                            else:
                                TasksCache.update(venv_id, {"type": "error", "code": r.status_code, "message": "download venv[%s] failed" % venv_id})
                                LOG.warning("download[%s] status: %s", venv_id, r.status_code)
                        except OperationFailedError as e:
                            TasksCache.update(app_id, {"type": "error", "code": 400, "message": "download venv[%s] failed" % venv_id, "result": e})
                            LOG.warning("download[%s] message: %s", venv_id, e)
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
        logger.config_logging(file_name = "venvs_manager.log",
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
                command, venv_id = self.pipe_client.recv()
                if command == Command.check_venv:
                    ready = False
                    try:
                        LOG.debug("check venv, venv_id: %s", venv_id)
                        r = lpl.venv_info(venv_id)
                        if r and "venv_info" in r:
                            venv_info = r["venv_info"]
                            venv_base_path = os.path.join(self.config["data_path"], "venvs", venv_id[:2], venv_id[2:4], venv_id)
                            venv_tar_path = os.path.join(venv_base_path, "venv.tar.gz")
                            venv_zip_path = os.path.join(venv_base_path, "venv.zip")
                            venv_path = os.path.join(venv_base_path, "venv")
                            # check venv.tar.gz
                            if os.path.exists(venv_tar_path) and os.path.isfile(venv_tar_path):
                                if venv_info["sha1"] != file_sha1sum(venv_tar_path):
                                    # download venv.tar.gz && extract venv.tar.gz
                                    pass
                                else:
                                    if not os.path.exists(venv_path):
                                        # extract venv.tar.gz
                                        pass
                                    else:
                                        ready = True
                            # check venv.zip
                            if os.path.exists(venv_zip_path) and os.path.isfile(venv_zip_path):
                                if venv_info["sha1"] != file_sha1sum(venv_zip_path):
                                    # download venv.zip && extract venv.zip
                                    pass
                                else:
                                    if not os.path.exists(venv_path):
                                        # extract venv.tar.gz
                                        pass
                                    else:
                                        ready = True
                            # download venv.tar.gz && extract venv.tar.gz
                            if ready:
                                status = TasksCache.peek(venv_id)
                                if status is not None:
                                    ready = False
                            else:
                                status = TasksCache.peek(venv_id)
                                if isinstance(status, dict):
                                    ready = status
                                    TasksCache.remove(venv_id)
                                elif status is None:
                                    TasksCache.set(venv_id)
                    except Exception as e:
                        LOG.exception(e)
                        ready = {"type": "error", "message": "get venv[%s] info failed: %s" % (venv_id, str(e))}
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
    def check_venv(self, venv_id):
        result = False
        LOG.debug("start check venv, venv_id: %s", venv_id)
        with (yield ManagerClient.write_lock.acquire()):
            LOG.debug("get check venv lock, venv_id: %s", venv_id)
            ManagerClient.process_dict["manager"][1].send((Command.check_venv, venv_id))
            LOG.debug("send check venv, venv_id: %s", venv_id)
            while not ManagerClient.process_dict["manager"][1].poll():
                yield gen.moment
            LOG.debug("recv check venv, venv_id: %s", venv_id)
            r = ManagerClient.process_dict["manager"][1].recv()
            LOG.debug("end check venv, venv_id: %s, r: %s", venv_id, r)
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
