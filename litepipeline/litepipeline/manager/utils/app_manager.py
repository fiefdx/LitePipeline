# -*- coding: utf-8 -*-

import os
import time
import logging
import shutil
import tarfile
import zipfile

from litepipeline.manager.models.applications import Applications
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, splitall
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class AppManagerBase(object):
    def __init__(self):
        pass

    def create(self, name, description, source_path):
        pass

    def update(self, app_id):
        pass

    def list(self):
        pass

    def info(self, app_id):
        pass

    def delete(self, app_id, version = None):
        pass

    def open(self, app_id, version = None):
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

    def app_path(self, app_id):
        return os.path.join(self.root_path, "applications", app_id[:2], app_id[2:4], app_id)

    def create(self, name, description, source_path):
        sha1 = file_sha1sum(source_path)
        LOG.debug("sha1: %s, %s", sha1, type(sha1))
        app_id = Applications.instance().add(name, sha1, description = description)
        app_path = self.app_path(app_id)
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
                app_path = self.app_path(app_id)
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
                if not success:
                    result = False
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset, limit, filters = {}):
        return Applications.instance().list(offset = offset, limit = limit, filters = filters)

    def info(self, app_id):
        return Applications.instance().get(app_id)

    def delete(self, app_id, version = None):
        result = False
        try:
            success = Applications.instance().delete(app_id)
            if success:
                app_path = self.app_path(app_id)
                if os.path.exists(app_path):
                    shutil.rmtree(app_path)
                    LOG.debug("remove directory: %s", app_path)
                result = True
        except Exception as e:
            LOG.exception(e)
        return result

    def open(self, app_id, version = None):
        result = False
        try:
            app_path = os.path.join(self.app_path(app_id), "app.tar.gz")
            if os.path.exists(app_path) and os.path.isfile(app_path):
                result = open(app_path, "rb")
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        pass