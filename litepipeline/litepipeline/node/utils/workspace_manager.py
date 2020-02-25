# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import shutil
import tarfile
import signal
from pathlib import Path
import threading
from threading import Thread, Lock
from multiprocessing import Process, Queue, Pipe

from tornado import gen, locks
import requests

from litepipeline.node.utils.common import file_sha1sum, splitall, get_workspace_path
from litepipeline.node.config import CONFIG
from litepipeline.node import logger

LOG = logging.getLogger(__name__)


class Command(object):
    pack_workspace = "pack_workspace"
    force_pack_workspace = "force_pack_workspace"
    exit = "exit"


class TasksCache(object):
    tasks = {}
    tasks_lock = Lock()

    @classmethod
    def set(cls, workspace):
        cls.tasks_lock.acquire()
        if workspace not in cls.tasks:
            cls.tasks[workspace] = False
        cls.tasks_lock.release()

    @classmethod
    def exists(cls, workspace):
        result = False
        cls.tasks_lock.acquire()
        if workspace in cls.tasks:
            result = True
        cls.tasks_lock.release()
        return result

    @classmethod
    def get(cls):
        result = False
        cls.tasks_lock.acquire()
        try:
            for workspace in cls.tasks:
                if not cls.tasks[workspace]:
                    cls.tasks[workspace] = True
                    result = workspace
                    break
        except Exception as e:
            LOG.exception(e)
        cls.tasks_lock.release()
        return result

    @classmethod
    def remove(cls, workspace):
        cls.tasks_lock.acquire()
        del cls.tasks[workspace]
        cls.tasks_lock.release()


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


class WorkerThread(StoppableThread):
    def __init__(self, pid):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid

    def run(self):
        LOG = logging.getLogger("worker")
        LOG.info("Worker(%03d) start", self.pid)
        try:
            while not self.stopped():
                try:
                    workspace = TasksCache.get()
                    if workspace:
                        path_parts = splitall(workspace)
                        task_id = path_parts[-2]
                        action_name = path_parts[-1]
                        tar_workspace = os.path.join(CONFIG["data_path"], "tmp", "download", "%s.%s.tar.gz" % (task_id, action_name))
                        tar_workspace_tmp = os.path.join(CONFIG["data_path"], "tmp", "download", "%s.%s.tmp.tar.gz" % (task_id, action_name))
                        if os.path.exists(tar_workspace_tmp) and os.path.isfile(tar_workspace_tmp):
                            os.remove(tar_workspace_tmp)
                        if os.path.exists(tar_workspace) and os.path.isfile(tar_workspace):
                            os.remove(tar_workspace)
                        t = tarfile.open(tar_workspace_tmp, mode = "x:gz")
                        t.add(workspace, arcname = "%s.%s" % (task_id, action_name))
                        t.close()
                        os.rename(tar_workspace_tmp, tar_workspace)
                        TasksCache.remove(workspace)
                    else:
                        time.sleep(0.5)
                except Exception as e:
                    LOG.exception(e)
        except Exception as e:
            LOG.exception(e)
        LOG.info("Worker(%03d) exit", self.pid)


class Manager(Process):
    def __init__(self, pipe_client, worker_num):
        Process.__init__(self)
        self.pipe_client = pipe_client
        self.worker_num = worker_num

    def run(self):
        logger.config_logging(file_name = "workspace_manager.log",
                              log_level = "NOSET",
                              dir_name = CONFIG["log_path"],
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
                t = WorkerThread(i)
                t.start()
                threads.append(t)

            while True:
                LOG.debug("Manager main loop")
                command, task_id, create_at, action_name = self.pipe_client.recv()
                if command == Command.pack_workspace:
                    ready = False
                    try:
                        LOG.debug("pack workspace, task_id: %s, action_name: %s", task_id, action_name)
                        workspace = get_workspace_path(create_at, task_id, action_name)
                        tar_workspace = os.path.join(CONFIG["data_path"], "tmp", "download", "%s.%s.tar.gz" % (task_id, action_name))
                        if os.path.exists(tar_workspace) and os.path.isfile(tar_workspace):
                            ready = True
                        # archive workspace
                        if not ready:
                            TasksCache.set(workspace)
                    except Exception as e:
                        LOG.exception(e)
                    self.pipe_client.send((command, ready))
                if command == Command.force_pack_workspace:
                    ready = False
                    try:
                        LOG.debug("force pack workspace, task_id: %s, action_name: %s", task_id, action_name)
                        workspace = get_workspace_path(create_at, task_id, action_name)
                        tar_workspace = os.path.join(CONFIG["data_path"], "tmp", "download", "%s.%s.tar.gz" % (task_id, action_name))
                        if os.path.exists(tar_workspace) and os.path.isdir(tar_workspace):
                            os.remove(tar_workspace)
                        # archive workspace
                        if not ready:
                            TasksCache.set(workspace)
                    except Exception as e:
                        LOG.exception(e)
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
            p = Manager(pipe_client, self.worker_num)
            p.daemon = True
            ManagerClient.process_list.append(p)
            ManagerClient.process_dict["manager"] = [p, pipe_master]
            p.start()
            ManagerClient._instance = self
        else:
            self.worker_num = ManagerClient._instance.worker_num

    @gen.coroutine
    def pack_workspace(self, task_id, create_at, action_name, force = False):
        result = False
        LOG.debug("start pack workspace, task_id: %s, create_at: %s, action_name: %s", task_id, create_at, action_name)
        with (yield ManagerClient.write_lock.acquire()):
            LOG.debug("get pack workspace lock, task_id: %s, action_name: %s", task_id, action_name)
            if force:
                ManagerClient.process_dict["manager"][1].send((Command.force_pack_workspace, task_id, create_at, action_name))
            else:
                ManagerClient.process_dict["manager"][1].send((Command.pack_workspace, task_id, create_at, action_name))
            LOG.debug("send pack workspace, task_id: %s, create_at: %s, action_name: %s, force: %s", task_id, create_at, action_name, force)
            while not ManagerClient.process_dict["manager"][1].poll():
                yield gen.moment
            LOG.debug("recv pack workspace, task_id: %s, action_name: %s", task_id, action_name)
            r = ManagerClient.process_dict["manager"][1].recv()
            LOG.debug("end pack workspace, task_id: %s, action_name: %s, r: %s", task_id, action_name, r)
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    def close(self):
        try:
            LOG.info("close ManagerClient")
            ManagerClient.process_dict["manager"][1].send((Command.exit, None, None, None))
            for p in ManagerClient.process_list[1:]:
                p.terminate()
            for p in ManagerClient.process_list:
                while p.is_alive():
                    time.sleep(0.5)
                    LOG.debug("sleep 0.5 second")
            LOG.info("All Process Exit!")
        except Exception as e:
            LOG.exception(e)
