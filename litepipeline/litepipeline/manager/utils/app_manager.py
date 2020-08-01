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

from litepipeline.manager.models.applications import Applications
from litepipeline.manager.models.application_history import ApplicationHistory
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, splitall
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class AppManagerBase(object):
    def __init__(self):
        pass

    def create(self, name, description, source_path):
        pass

    def update(self, app_id, name, description, source_path):
        pass

    def list(self, offset, limit, filters = {}):
        pass

    def list_history(self, offset, limit, filters = {}):
        pass

    def info(self, app_id):
        pass

    def info_history(self, history_id, app_id = ""):
        pass

    def activate_history(self, history_id, app_id = ""):
        pass

    def delete(self, app_id):
        pass

    def delete_history(self, history_id, app_id):
        pass

    def get_app_config(self, app_id, sha1):
        pass

    def open(self, app_id, sha1):
        pass

    def close(self):
        pass


class AppLocalTarGzManager(AppManagerBase):
    _instance = None
    name = "AppLocalTarGzManager"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.root_path = CONFIG["data_path"]
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def make_app_path(self, app_id):
        return os.path.join(self.root_path, "applications", app_id[:2], app_id[2:4], app_id)

    def make_app_version_path(self, app_id, sha1):
        return os.path.join(self.make_app_path(app_id), sha1)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        app_id = Applications.instance().add(name, sha1, description = description)
        app_path = self.make_app_version_path(app_id, sha1)
        if os.path.exists(app_path):
            shutil.rmtree(app_path)
        os.makedirs(app_path)
        shutil.copy2(source_path, os.path.join(app_path, "app.tar.gz"))
        os.remove(source_path)
        if os.path.exists(os.path.join(app_path, "app")):
            shutil.rmtree(os.path.join(app_path, "app"))
        t = tarfile.open(os.path.join(app_path, "app.tar.gz"), "r")
        t.extractall(app_path)
        path_parts = splitall(t.getnames()[0])
        tar_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
        t.close()
        os.rename(os.path.join(app_path, tar_root_name), os.path.join(app_path, "app"))
        ApplicationHistory.instance().add(app_id, sha1, description = description)
        return app_id

    def update(self, app_id, name, description, source_path):
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
                app_path = self.make_app_version_path(app_id, sha1)
                if os.path.exists(app_path):
                    shutil.rmtree(app_path)
                os.makedirs(app_path)
                shutil.copy2(source_path, os.path.join(app_path, "app.tar.gz"))
                os.remove(source_path)
                if os.path.exists(os.path.join(app_path, "app")):
                    shutil.rmtree(os.path.join(app_path, "app"))
                t = tarfile.open(os.path.join(app_path, "app.tar.gz"), "r")
                t.extractall(app_path)
                tar_root_name = splitall(t.getnames()[0])[0]
                os.rename(os.path.join(app_path, tar_root_name), os.path.join(app_path, "app"))
                need_update = True
            if data or need_update:
                success = Applications.instance().update(app_id, data)
                if success:
                    if "sha1" in data:
                        description = "" if "description" not in data else data["description"]
                        ApplicationHistory.instance().add(app_id, data["sha1"], description = description)
                else:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Applications.instance().list(offset = offset, limit = limit, filters = filters)

    def list_history(self, offset, limit, filters = {}):
        return ApplicationHistory.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, app_id):
        return Applications.instance().get(app_id)

    def info_history(self, history_id, app_id = ""):
        return ApplicationHistory.instance().get(history_id, app_id = app_id)

    def activate_history(self, history_id, app_id = ""):
        result = False
        try:
            if app_id:
                history = self.info_history(history_id, app_id = app_id)
                if history:
                    data = {"sha1": history["sha1"]}
                    if history["description"]:
                        data["description"] = history["description"]
                    success = Applications.instance().update(app_id, data)
                    if success:
                        result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete(self, app_id):
        result = False
        try:
            success = Applications.instance().delete(app_id)
            if success:
                ApplicationHistory.instance().delete_by_app_id(app_id)
                app_path = self.make_app_path(app_id)
                if os.path.exists(app_path):
                    shutil.rmtree(app_path)
                    LOG.debug("remove directory: %s", app_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete_history(self, history_id, app_id):
        result = False
        try:
            history = ApplicationHistory.instance().delete_by_history_id_app_id(history_id, app_id)
            if history and history is not None:
                filters = ApplicationHistory.instance().parse_filters({"app_id": history["application_id"], "sha1": history["sha1"]})
                num = ApplicationHistory.instance().count(filters)
                if num == 0:
                    app_path = self.make_app_version_path(history["application_id"], history["sha1"])
                    if os.path.exists(app_path):
                        shutil.rmtree(app_path)
                        LOG.debug("remove directory: %s", app_path)
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def get_app_config(self, app_id, sha1):
        result = False
        try:
            app_config_path = os.path.join(self.make_app_version_path(app_id, sha1), "app", "configuration.json")
            if os.path.exists(app_config_path):
                fp = open(app_config_path, "r")
                result = json.loads(fp.read())
                fp.close()
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, app_id, sha1):
        result = False
        try:
            app_path = os.path.join(self.make_app_version_path(app_id, sha1), "app.tar.gz")
            if os.path.exists(app_path) and os.path.isfile(app_path):
                result = open(app_path, "rb")
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass


class AppLocalZipManager(AppManagerBase):
    _instance = None
    name = "AppLocalZipManager"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.root_path = CONFIG["data_path"]
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def make_app_path(self, app_id):
        return os.path.join(self.root_path, "applications", app_id[:2], app_id[2:4], app_id)

    def make_app_version_path(self, app_id, sha1):
        return os.path.join(self.make_app_path(app_id), sha1)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        app_id = Applications.instance().add(name, sha1, description = description)
        app_path = self.make_app_version_path(app_id, sha1)
        if os.path.exists(app_path):
            shutil.rmtree(app_path)
        os.makedirs(app_path)
        shutil.copy2(source_path, os.path.join(app_path, "app.zip"))
        os.remove(source_path)
        ApplicationHistory.instance().add(app_id, sha1, description = description)
        return app_id

    def update(self, app_id, name, description, source_path):
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
                app_path = self.make_app_version_path(app_id, sha1)
                if os.path.exists(app_path):
                    shutil.rmtree(app_path)
                os.makedirs(app_path)
                shutil.copy2(source_path, os.path.join(app_path, "app.zip"))
                os.remove(source_path)
                need_update = True
            if data or need_update:
                success = Applications.instance().update(app_id, data)
                if success:
                    if "sha1" in data:
                        description = "" if "description" not in data else data["description"]
                        ApplicationHistory.instance().add(app_id, data["sha1"], description = description)
                else:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Applications.instance().list(offset = offset, limit = limit, filters = filters)

    def list_history(self, offset, limit, filters = {}):
        return ApplicationHistory.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, app_id):
        return Applications.instance().get(app_id)

    def info_history(self, history_id, app_id = ""):
        return ApplicationHistory.instance().get(history_id, app_id = app_id)

    def activate_history(self, history_id, app_id = ""):
        result = False
        try:
            if app_id:
                history = self.info_history(history_id, app_id = app_id)
                if history:
                    data = {"sha1": history["sha1"]}
                    if history["description"]:
                        data["description"] = history["description"]
                    success = Applications.instance().update(app_id, data)
                    if success:
                        result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete(self, app_id):
        result = False
        try:
            success = Applications.instance().delete(app_id)
            if success:
                ApplicationHistory.instance().delete_by_app_id(app_id)
                app_path = self.make_app_path(app_id)
                if os.path.exists(app_path):
                    shutil.rmtree(app_path)
                    LOG.debug("remove directory: %s", app_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete_history(self, history_id, app_id):
        result = False
        try:
            history = ApplicationHistory.instance().delete_by_history_id_app_id(history_id, app_id)
            if history and history is not None:
                filters = ApplicationHistory.instance().parse_filters({"app_id": history["application_id"], "sha1": history["sha1"]})
                num = ApplicationHistory.instance().count(filters)
                if num == 0:
                    app_path = self.make_app_version_path(history["application_id"], history["sha1"])
                    if os.path.exists(app_path):
                        shutil.rmtree(app_path)
                        LOG.debug("remove directory: %s", app_path)
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def get_app_config(self, app_id, sha1):
        result = False
        try:
            app_path = os.path.join(self.make_app_version_path(app_id, sha1), "app.zip")
            if os.path.exists(app_path):
                z = zipfile.ZipFile(app_path)
                path_parts = splitall(z.namelist()[0])
                root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                app_config_path = os.path.join(root_name, "configuration.json")
                result = json.loads(z.read(app_config_path).decode("utf-8"))
                z.close()
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, app_id, sha1):
        result = False
        try:
            app_path = os.path.join(self.make_app_version_path(app_id, sha1), "app.zip")
            if os.path.exists(app_path) and os.path.isfile(app_path):
                result = open(app_path, "rb")
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass


class AppLDFSZipManager(AppManagerBase):
    _instance = None
    name = "AppLocalZipManager"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.root_path = os.path.join("/litemanager_%s:%s" % (CONFIG["http_host"], CONFIG["http_port"]), "data")
            cls._instance.ldfs = LiteDFSClient(CONFIG["ldfs_http_host"], CONFIG["ldfs_http_port"])
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def make_app_path(self, app_id):
        return os.path.join(self.root_path, "applications", app_id[:2], app_id[2:4], app_id)

    def make_app_version_path(self, app_id, sha1):
        return os.path.join(self.make_app_path(app_id), sha1)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        app_id = Applications.instance().add(name, sha1, description = description)
        app_path = self.make_app_version_path(app_id, sha1)
        self.ldfs.delete_directory(app_path)
        self.ldfs.create_file(source_path, os.path.join(app_path, "app.zip"), replica = 1)
        os.remove(source_path)
        ApplicationHistory.instance().add(app_id, sha1, description = description)
        return app_id

    def update(self, app_id, name, description, source_path):
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
                app_path = self.make_app_version_path(app_id, sha1)
                self.ldfs.delete_directory(app_path)
                self.ldfs.create_file(source_path, os.path.join(app_path, "app.zip"), replica = 1)
                os.remove(source_path)
                need_update = True
            if data or need_update:
                success = Applications.instance().update(app_id, data)
                if success:
                    if "sha1" in data:
                        description = "" if "description" not in data else data["description"]
                        ApplicationHistory.instance().add(app_id, data["sha1"], description = description)
                else:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Applications.instance().list(offset = offset, limit = limit, filters = filters)

    def list_history(self, offset, limit, filters = {}):
        return ApplicationHistory.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, app_id):
        return Applications.instance().get(app_id)

    def info_history(self, history_id, app_id = ""):
        return ApplicationHistory.instance().get(history_id, app_id = app_id)

    def activate_history(self, history_id, app_id = ""):
        result = False
        try:
            if app_id:
                history = self.info_history(history_id, app_id = app_id)
                if history:
                    data = {"sha1": history["sha1"]}
                    if history["description"]:
                        data["description"] = history["description"]
                    success = Applications.instance().update(app_id, data)
                    if success:
                        result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete(self, app_id):
        result = False
        try:
            success = Applications.instance().delete(app_id)
            if success:
                ApplicationHistory.instance().delete_by_app_id(app_id)
                app_path = self.make_app_path(app_id)
                self.ldfs.delete_directory(app_path)
                LOG.debug("remove ldfs directory: %s", app_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def delete_history(self, history_id, app_id):
        result = False
        try:
            history = ApplicationHistory.instance().delete_by_history_id_app_id(history_id, app_id)
            if history and history is not None:
                filters = ApplicationHistory.instance().parse_filters({"app_id": history["application_id"], "sha1": history["sha1"]})
                num = ApplicationHistory.instance().count(filters)
                if num == 0:
                    app_path = self.make_app_version_path(history["application_id"], history["sha1"])
                    self.ldfs.delete_directory(app_path)
                    LOG.debug("remove ldfs directory: %s", app_path)
            result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def get_app_config(self, app_id, sha1):
        result = False
        try:
            app_path = os.path.join(self.make_app_version_path(app_id, sha1), "app.zip")
            remote_file = self.ldfs.open_remote_file(app_path)
            if remote_file:
                z = zipfile.ZipFile(remote_file)
                path_parts = splitall(z.namelist()[0])
                root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                app_config_path = os.path.join(root_name, "configuration.json")
                result = json.loads(z.read(app_config_path).decode("utf-8"))
                z.close()
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, app_id, sha1):
        result = False
        try:
            app_path = os.path.join(self.make_app_version_path(app_id, sha1), "app.zip")
            remote_file = self.ldfs.open_remote_file(app_path)
            if remote_file:
                result = io.BufferedReader(remote_file, buffer_size = 1024 * 1024)
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass


class AppManager(object):
    _instance = None
    name = "AppManager"

    def __new__(cls):
        if not cls._instance:
            if "app_store" in CONFIG:
                if CONFIG["app_store"] == "local.tar.gz":
                    cls._instance = AppLocalTarGzManager()
                elif CONFIG["app_store"] == "local.zip":
                    cls._instance = AppLocalZipManager()
                elif CONFIG["app_store"] == "ldfs.zip":
                    cls._instance = AppLDFSZipManager()
                else:
                    cls._instance = AppLocalZipManager()
            else:
                cls._instance = AppLocalZipManager()
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance
