# -*- coding: utf-8 -*-

import os
import io
import time
import json
import logging
import shutil
import tarfile
import zipfile

from litedfs_client.client import LiteDFSClient

from litepipeline.manager.models.venvs import Venvs
from litepipeline.manager.models.venv_history import VenvHistory
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, splitall
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class VenvManagerBase(object):
    def __init__(self):
        pass

    def create(self, name, description, source_path):
        pass

    def update(self, venv_id, name, description, source_path):
        pass

    def list(self, offset, limit, filters = {}):
        pass

    def list_history(self, offset, limit, filters = {}):
        pass

    def info(self, venv_id):
        pass

    def info_history(self, history_id, venv_id = ""):
        pass

    def activate_history(self, history_id, venv_id = ""):
        pass

    def delete(self, venv_id):
        pass

    def delete_history(self, history_id, venv_id):
        pass

    def get_venv_config(self, venv_id, sha1):
        pass

    def open(self, venv_id, sha1):
        pass

    def close(self):
        pass


class VenvLocalTarGzManager(VenvManagerBase):
    _instance = None
    name = "VenvLocalTarGzManager"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.root_path = CONFIG["data_path"]
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def make_venv_path(self, venv_id):
        return os.path.join(self.root_path, "venvs", venv_id[:2], venv_id[2:4], venv_id)

    def make_venv_version_path(self, venv_id, sha1):
        return os.path.join(self.make_venv_path(venv_id), sha1)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        venv_id = Venvs.instance().add(name, sha1, description = description)
        venv_path = self.make_venv_version_path(venv_id, sha1)
        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
        os.makedirs(venv_path)
        shutil.copy2(source_path, os.path.join(venv_path, "venv.tar.gz"))
        os.remove(source_path)
        VenvHistory.instance().add(venv_id, sha1, description = description)
        return venv_id

    def update(self, venv_id, name, description, source_path):
        result = True
        try:
            data = {}
            need_update = False
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if os.path.exists(source_path) and os.path.isfile(source_path):
                sha1 = file_sha1sum(source_path)
                data["sha1"] = sha1
                LOG.debug("sha1: %s, %s", sha1, type(sha1))
                venv_path = self.make_venv_version_path(venv_id, sha1)
                if os.path.exists(venv_path):
                    shutil.rmtree(venv_path)
                os.makedirs(venv_path)
                shutil.copy2(source_path, os.path.join(venv_path, "venv.tar.gz"))
                os.remove(source_path)
                need_update = True
            if data or need_update:
                success = Venvs.instance().update(venv_id, data)
                if success:
                    if "sha1" in data:
                        description = "" if "description" not in data else data["description"]
                        VenvHistory.instance().add(venv_id, data["sha1"], description = description)
                else:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Venvs.instance().list(offset = offset, limit = limit, filters = filters)

    def list_history(self, offset, limit, filters = {}):
        return VenvHistory.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, venv_id):
        return Venvs.instance().get(venv_id)

    def info_history(self, history_id, venv_id = ""):
        return VenvHistory.instance().get(history_id, venv_id = venv_id)

    def activate_history(self, history_id, venv_id = ""):
        result = False
        try:
            if venv_id:
                history = self.info_history(history_id, venv_id = venv_id)
                if history:
                    data = {"sha1": history["sha1"]}
                    if history["description"]:
                        data["description"] = history["description"]
                    success = Venvs.instance().update(venv_id, data)
                    if success:
                        result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete(self, venv_id):
        result = False
        try:
            success = Venvs.instance().delete(venv_id)
            if success:
                VenvHistory.instance().delete_by_venv_id(venv_id)
                venv_path = self.make_venv_path(venv_id)
                if os.path.exists(venv_path):
                    shutil.rmtree(venv_path)
                    LOG.debug("remove directory: %s", venv_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete_history(self, history_id, venv_id):
        result = False
        try:
            history = VenvHistory.instance().delete_by_history_id_venv_id(history_id, venv_id)
            if history and history is not None:
                filters = VenvHistory.instance().parse_filters({"venv_id": history["venv_id"], "sha1": history["sha1"]})
                num = VenvHistory.instance().count(filters)
                if num == 0:
                    venv_path = self.make_venv_version_path(history["venv_id"], history["sha1"])
                    if os.path.exists(venv_path):
                        shutil.rmtree(venv_path)
                        LOG.debug("remove directory: %s", venv_path)
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, venv_id, sha1):
        result = False
        try:
            venv_path = os.path.join(self.make_venv_version_path(venv_id, sha1), "venv.tar.gz")
            if os.path.exists(venv_path) and os.path.isfile(venv_path):
                result = open(venv_path, "rb")
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass


class VenvLocalZipManager(VenvManagerBase):
    _instance = None
    name = "VenvLocalZipManager"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.root_path = CONFIG["data_path"]
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def make_venv_path(self, venv_id):
        return os.path.join(self.root_path, "venvs", venv_id[:2], venv_id[2:4], venv_id)

    def make_venv_version_path(self, venv_id, sha1):
        return os.path.join(self.make_venv_path(venv_id), sha1)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        venv_id = Venvs.instance().add(name, sha1, description = description)
        venv_path = self.make_venv_version_path(venv_id, sha1)
        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
        os.makedirs(venv_path)
        shutil.copy2(source_path, os.path.join(venv_path, "venv.zip"))
        os.remove(source_path)
        VenvHistory.instance().add(venv_id, sha1, description = description)
        return venv_id

    def update(self, venv_id, name, description, source_path):
        result = True
        try:
            data = {}
            need_update = False
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if os.path.exists(source_path) and os.path.isfile(source_path):
                sha1 = file_sha1sum(source_path)
                data["sha1"] = sha1
                LOG.debug("sha1: %s, %s", sha1, type(sha1))
                venv_path = self.make_venv_version_path(venv_id, sha1)
                if os.path.exists(venv_path):
                    shutil.rmtree(venv_path)
                os.makedirs(venv_path)
                shutil.copy2(source_path, os.path.join(venv_path, "venv.zip"))
                os.remove(source_path)
                need_update = True
            if data or need_update:
                success = Venvs.instance().update(venv_id, data)
                if success:
                    if "sha1" in data:
                        description = "" if "description" not in data else data["description"]
                        VenvHistory.instance().add(venv_id, data["sha1"], description = description)
                else:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Venvs.instance().list(offset = offset, limit = limit, filters = filters)

    def list_history(self, offset, limit, filters = {}):
        return VenvHistory.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, venv_id):
        return Venvs.instance().get(venv_id)

    def info_history(self, history_id, venv_id = ""):
        return VenvHistory.instance().get(history_id, venv_id = venv_id)

    def activate_history(self, history_id, venv_id = ""):
        result = False
        try:
            if venv_id:
                history = self.info_history(history_id, venv_id = venv_id)
                if history:
                    data = {"sha1": history["sha1"]}
                    if history["description"]:
                        data["description"] = history["description"]
                    success = Venvs.instance().update(venv_id, data)
                    if success:
                        result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete(self, venv_id):
        result = False
        try:
            success = Venvs.instance().delete(venv_id)
            if success:
                VenvHistory.instance().delete_by_venv_id(venv_id)
                venv_path = self.make_venv_path(venv_id)
                if os.path.exists(venv_path):
                    shutil.rmtree(venv_path)
                    LOG.debug("remove directory: %s", venv_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete_history(self, history_id, venv_id):
        result = False
        try:
            history = VenvHistory.instance().delete_by_history_id_venv_id(history_id, venv_id)
            if history and history is not None:
                filters = VenvHistory.instance().parse_filters({"venv_id": history["venv_id"], "sha1": history["sha1"]})
                num = VenvHistory.instance().count(filters)
                if num == 0:
                    venv_path = self.make_venv_version_path(history["venv_id"], history["sha1"])
                    if os.path.exists(venv_path):
                        shutil.rmtree(venv_path)
                        LOG.debug("remove directory: %s", venv_path)
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, venv_id, sha1):
        result = False
        try:
            venv_path = os.path.join(self.make_venv_version_path(venv_id, sha1), "venv.zip")
            if os.path.exists(venv_path) and os.path.isfile(venv_path):
                result = open(venv_path, "rb")
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass


class VenvLDFSTarGzManager(VenvManagerBase):
    _instance = None
    name = "VenvLDFSTarGzManager"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.root_path = os.path.join("/litemanager_%s:%s" % (CONFIG["http_host"], CONFIG["http_port"]), "data")
            cls._instance.ldfs = LiteDFSClient(CONFIG["ldfs_http_host"], CONFIG["ldfs_http_port"])
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def make_venv_path(self, venv_id):
        return os.path.join(self.root_path, "venvs", venv_id[:2], venv_id[2:4], venv_id)

    def make_venv_version_path(self, venv_id, sha1):
        return os.path.join(self.make_venv_path(venv_id), sha1)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        venv_id = Venvs.instance().add(name, sha1, description = description)
        venv_path = self.make_venv_version_path(venv_id, sha1)
        self.ldfs.delete_directory(venv_path)
        self.ldfs.create_file(source_path, os.path.join(venv_path, "venv.tar.gz"), replica = 1)
        os.remove(source_path)
        VenvHistory.instance().add(venv_id, sha1, description = description)
        return venv_id

    def update(self, venv_id, name, description, source_path):
        result = True
        try:
            data = {}
            need_update = False
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if os.path.exists(source_path) and os.path.isfile(source_path):
                sha1 = file_sha1sum(source_path)
                data["sha1"] = sha1
                LOG.debug("sha1: %s, %s", sha1, type(sha1))
                venv_path = self.make_venv_version_path(venv_id, sha1)
                self.ldfs.delete_directory(venv_path)
                self.ldfs.create_file(source_path, os.path.join(venv_path, "venv.tar.gz"), replica = 1)
                os.remove(source_path)
                need_update = True
            if data or need_update:
                success = Venvs.instance().update(venv_id, data)
                if success:
                    if "sha1" in data:
                        description = "" if "description" not in data else data["description"]
                        VenvHistory.instance().add(venv_id, data["sha1"], description = description)
                else:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Venvs.instance().list(offset = offset, limit = limit, filters = filters)

    def list_history(self, offset, limit, filters = {}):
        return VenvHistory.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, venv_id):
        return Venvs.instance().get(venv_id)

    def info_history(self, history_id, venv_id = ""):
        return VenvHistory.instance().get(history_id, venv_id = venv_id)

    def activate_history(self, history_id, venv_id = ""):
        result = False
        try:
            if venv_id:
                history = self.info_history(history_id, venv_id = venv_id)
                if history:
                    data = {"sha1": history["sha1"]}
                    if history["description"]:
                        data["description"] = history["description"]
                    success = Venvs.instance().update(venv_id, data)
                    if success:
                        result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete(self, venv_id):
        result = False
        try:
            success = Venvs.instance().delete(venv_id)
            if success:
                VenvHistory.instance().delete_by_venv_id(venv_id)
                venv_path = self.make_venv_path(venv_id)
                self.ldfs.delete_directory(venv_path)
                LOG.debug("remove ldfs directory: %s", venv_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete_history(self, history_id, venv_id):
        result = False
        try:
            history = VenvHistory.instance().delete_by_history_id_venv_id(history_id, venv_id)
            if history and history is not None:
                filters = VenvHistory.instance().parse_filters({"venv_id": history["venv_id"], "sha1": history["sha1"]})
                num = VenvHistory.instance().count(filters)
                if num == 0:
                    venv_path = self.make_venv_version_path(history["venv_id"], history["sha1"])
                    self.ldfs.delete_directory(venv_path)
                    LOG.debug("remove ldfs directory: %s", venv_path)
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, venv_id, sha1):
        result = False
        try:
            venv_path = os.path.join(self.make_venv_version_path(venv_id, sha1), "venv.tar.gz")
            remote_file = self.ldfs.open_remote_file(venv_path)
            if remote_file:
                result = io.BufferedReader(remote_file, buffer_size = 1024 * 1024)
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass


class VenvLDFSZipManager(VenvManagerBase):
    _instance = None
    name = "VenvLDFSZipManager"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.root_path = os.path.join("/litemanager_%s:%s" % (CONFIG["http_host"], CONFIG["http_port"]), "data")
            cls._instance.ldfs = LiteDFSClient(CONFIG["ldfs_http_host"], CONFIG["ldfs_http_port"])
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def make_venv_path(self, venv_id):
        return os.path.join(self.root_path, "venvs", venv_id[:2], venv_id[2:4], venv_id)

    def make_venv_version_path(self, venv_id, sha1):
        return os.path.join(self.make_venv_path(venv_id), sha1)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        venv_id = Venvs.instance().add(name, sha1, description = description)
        venv_path = self.make_venv_version_path(venv_id, sha1)
        self.ldfs.delete_directory(venv_path)
        self.ldfs.create_file(source_path, os.path.join(venv_path, "venv.zip"), replica = 1)
        os.remove(source_path)
        VenvHistory.instance().add(venv_id, sha1, description = description)
        return venv_id

    def update(self, venv_id, name, description, source_path):
        result = True
        try:
            data = {}
            need_update = False
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if os.path.exists(source_path) and os.path.isfile(source_path):
                sha1 = file_sha1sum(source_path)
                data["sha1"] = sha1
                LOG.debug("sha1: %s, %s", sha1, type(sha1))
                venv_path = self.make_venv_version_path(venv_id, sha1)
                self.ldfs.delete_directory(venv_path)
                self.ldfs.create_file(source_path, os.path.join(venv_path, "venv.zip"), replica = 1)
                os.remove(source_path)
                need_update = True
            if data or need_update:
                success = Venvs.instance().update(venv_id, data)
                if success:
                    if "sha1" in data:
                        description = "" if "description" not in data else data["description"]
                        VenvHistory.instance().add(venv_id, data["sha1"], description = description)
                else:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Venvs.instance().list(offset = offset, limit = limit, filters = filters)

    def list_history(self, offset, limit, filters = {}):
        return VenvHistory.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, venv_id):
        return Venvs.instance().get(venv_id)

    def info_history(self, history_id, venv_id = ""):
        return VenvHistory.instance().get(history_id, venv_id = venv_id)

    def activate_history(self, history_id, venv_id = ""):
        result = False
        try:
            if venv_id:
                history = self.info_history(history_id, venv_id = venv_id)
                if history:
                    data = {"sha1": history["sha1"]}
                    if history["description"]:
                        data["description"] = history["description"]
                    success = Venvs.instance().update(venv_id, data)
                    if success:
                        result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete(self, venv_id):
        result = False
        try:
            success = Venvs.instance().delete(venv_id)
            if success:
                VenvHistory.instance().delete_by_venv_id(venv_id)
                venv_path = self.make_venv_path(venv_id)
                self.ldfs.delete_directory(venv_path)
                LOG.debug("remove ldfs directory: %s", venv_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete_history(self, history_id, venv_id):
        result = False
        try:
            history = VenvHistory.instance().delete_by_history_id_venv_id(history_id, venv_id)
            if history and history is not None:
                filters = VenvHistory.instance().parse_filters({"venv_id": history["venv_id"], "sha1": history["sha1"]})
                num = VenvHistory.instance().count(filters)
                if num == 0:
                    venv_path = self.make_venv_version_path(history["venv_id"], history["sha1"])
                    self.ldfs.delete_directory(venv_path)
                    LOG.debug("remove ldfs directory: %s", venv_path)
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, venv_id, sha1):
        result = False
        try:
            venv_path = os.path.join(self.make_venv_version_path(venv_id, sha1), "venv.zip")
            remote_file = self.ldfs.open_remote_file(venv_path)
            if remote_file:
                result = io.BufferedReader(remote_file, buffer_size = 1024 * 1024)
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass


class VenvManager(object):
    _instance = None
    name = "VenvManager"

    def __new__(cls):
        if not cls._instance:
            if "venv_store" in CONFIG:
                if CONFIG["venv_store"] == "local.tar.gz":
                    cls._instance = VenvLocalTarGzManager()
                elif CONFIG["venv_store"] == "local.zip":
                    cls._instance = VenvLocalZipManager()
                elif CONFIG["venv_store"] == "ldfs.tar.gz":
                    cls._instance = VenvLDFSTarGzManager()
                elif CONFIG["venv_store"] == "ldfs.zip":
                    cls._instance = VenvLDFSZipManager()
                else:
                    cls._instance = VenvLocalTarGzManager()
            else:
                cls._instance = VenvLocalTarGzManager()
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance
