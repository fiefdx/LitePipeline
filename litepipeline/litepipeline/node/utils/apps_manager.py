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

from litepipeline.node.utils.common import file_sha1sum, splitall
from litepipeline.node.config import CONFIG
from litepipeline.node import logger

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
    def remove(cls, app_id):
        cls.tasks_lock.acquire()
        del cls.tasks[app_id]
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
                    app_id = TasksCache.get()
                    if app_id:
                        url = "http://%s:%s/app/download?app_id=%s" % (CONFIG["manager_http_host"], CONFIG["manager_http_port"], app_id)
                        file_path = os.path.join(CONFIG["data_path"], "tmp", "%s.tar.gz" % app_id)
                        LOG.debug("download: %s", url)
                        r = requests.get(url)
                        if r.status_code == 200:
                            LOG.debug("download[%s] status: %s", app_id, r.status_code)
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
                            path_parts = splitall(t.getnames()[0])
                            tar_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                            t.close()
                            app_config_path = os.path.join(app_path, tar_root_name, "configuration.json")
                            f = open(app_config_path, "r")
                            app_config = json.loads(f.read())
                            f.close()
                            venvs = set()
                            for action in app_config["actions"]:
                                if "env" in action:
                                    venvs.add(action["env"])
                            for venv in list(venvs):
                                venv_tar_path = os.path.join(app_path, tar_root_name, "%s.tar.gz" % venv)
                                venv_path = os.path.join(app_path, tar_root_name, venv)
                                if os.path.exists(venv_path):
                                    shutil.rmtree(venv_path)
                                os.makedirs(venv_path)
                                t = tarfile.open(venv_tar_path, "r")
                                t.extractall(venv_path)
                                t.close()
                            os.rename(os.path.join(app_path, tar_root_name), os.path.join(app_path, "app"))
                            TasksCache.remove(app_id)
                        else:
                            LOG.warning("download[%s] status: %s", app_id, r.status_code)
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
        logger.config_logging(file_name = "apps_manager.log",
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
                command, app_id, sha1 = self.pipe_client.recv()
                if command == Command.check_app:
                    ready = False
                    try:
                        LOG.debug("check app, app_id: %s, sha1: %s", app_id, sha1)
                        app_base_path = os.path.join(CONFIG["data_path"], "applications", app_id[:2], app_id[2:4], app_id)
                        app_tar_path = os.path.join(app_base_path, "app.tar.gz")
                        app_path = os.path.join(app_base_path, "app")
                        if os.path.exists(app_tar_path) and os.path.isfile(app_tar_path):
                            if sha1 != file_sha1sum(app_tar_path):
                                # download app.tar.gz && extract app.tar.gz
                                pass
                            else:
                                if not os.path.exists(app_path):
                                    # extract app.tar.gz
                                    pass
                                else:
                                    ready = True
                        # download app.tar.gz && extract app.tar.gz
                        if not ready:
                            TasksCache.set(app_id)
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
    def check_app(self, app_id, sha1):
        result = False
        LOG.debug("start check app, app_id: %s, sha1: %s", app_id, sha1)
        with (yield ManagerClient.write_lock.acquire()):
            LOG.debug("get check app lock, app_id: %s, sha1: %s", app_id, sha1)
            ManagerClient.process_dict["manager"][1].send((Command.check_app, app_id, sha1))
            LOG.debug("send check app, app_id: %s, sha1: %s", app_id, sha1)
            while not ManagerClient.process_dict["manager"][1].poll():
                yield gen.moment
            LOG.debug("recv check app, app_id: %s, sha1: %s", app_id, sha1)
            r = ManagerClient.process_dict["manager"][1].recv()
            LOG.debug("end check app, app_id: %s, sha1: %s, r: %s", app_id, sha1, r)
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    def close(self):
        try:
            LOG.info("close ManagerClient")
            ManagerClient.process_dict["manager"][1].send((Command.exit, None, None))
            for p in ManagerClient.process_list[1:]:
                p.terminate()
            for p in ManagerClient.process_list:
                while p.is_alive():
                    time.sleep(0.5)
                    LOG.debug("sleep 0.5 second")
            LOG.info("All Process Exit!")
        except Exception as e:
            LOG.exception(e)
