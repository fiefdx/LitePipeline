# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import urllib
import logging

import requests

from litepipeline_helper.version import __version__

LOG = logging.getLogger(__name__)

USER_AGENT = "python-litepipeline-client"


class OperationFailedError(Exception):
    def __init__(self, message):
        self.message = message


class LitePipelineClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.base_url = "http://%s:%s" % (self.host, self.port)
        self.headers = {"user-agent": "%s/%s" % (USER_AGENT, __version__)}

    def application_list(self, offset = 0, limit = 0, filters = {}):
        result = False
        url = "%s/app/list?offset=%s&limit=%s" % (self.base_url, offset, limit)
        if "name" in filters:
            url += "&name=%s" % urllib.parse.quote(filters["name"])
        if "id" in filters:
            url += "&id=%s" % filters["id"]
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application list failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_info(self, app_id, config = False):
        result = False
        config_str = "false"
        if config is True:
            config_str = "true"
        url = "%s/app/info?app_id=%s&config=%s" % (self.base_url, app_id, config_str)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_delete(self, app_id):
        result = False
        url = "%s/app/delete?app_id=%s" % (self.base_url, app_id)
        r = requests.delete(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_create(self, file_path, name, description = ""):
        result = False
        url = "%s/app/create" % self.base_url
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file_name = os.path.split(file_path)[-1]
            files = {'up_file': (file_name, open(file_path, "rb"), b"text/plain")}
            values = {"name": name, "description": description}
            r = requests.post(url, files = files, data = values, headers = self.headers)
            if r.status_code == 200:
                data = r.json()
                if "result" in data and data["result"] == "ok":
                    result = data
                else:
                    raise OperationFailedError("application create failed: %s" % data["result"])
            else:
                raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        else:
            raise OperationFailedError("file[%s] not exists" % file_path)
        return result

    def application_update(self, app_id, file_path = None, name = None, description = None):
        result = False
        url = "%s/app/update" % self.base_url
        files = {}
        values = {"app_id": app_id}
        if file_path is not None:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                file_name = os.path.split(file_path)[-1]
                files = {'up_file': (file_name, open(file_path, "rb"), b"text/plain")}
            else:
                raise OperationFailedError("file[%s] not exists" % file_path)
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description

        if files:
            r = requests.post(url, files = files, data = values, headers = self.headers)
        else:
            for key in values:
                values[key] = (None, values[key])
            r = requests.post(url, files = values, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application update failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_download(self, app_id, directory = ".", sha1 = ""):
        result = False
        url = "%s/app/download?app_id=%s&sha1=%s" % (self.base_url, app_id, sha1)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            file_type = "tar.gz"
            if "content-disposition" in r.headers:
                if "zip" in r.headers["content-disposition"]:
                    file_type = "zip"
            file_path = os.path.join(directory, "%s.%s" % (app_id, file_type))
            f = open(file_path, 'wb')
            f.write(r.content)
            f.close()
            result = file_path
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_history_list(self, app_id, offset = 0, limit = 0):
        result = False
        url = "%s/app/history/list?app_id=%s&offset=%s&limit=%s" % (self.base_url, app_id, offset, limit)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application history list failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_history_info(self, app_id, history_id, config = False):
        result = False
        config_str = "false"
        if config is True:
            config_str = "true"
        url = "%s/app/history/info?app_id=%s&history_id=%s&config=%s" % (self.base_url, app_id, history_id, config_str)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application history info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_history_activate(self, app_id, history_id):
        result = False
        url = "%s/app/history/activate" % self.base_url
        data = {"app_id": app_id, "history_id": history_id}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application history activate failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def application_history_delete(self, app_id, history_id):
        result = False
        url = "%s/app/history/delete?app_id=%s&history_id=%s" % (self.base_url, app_id, history_id)
        r = requests.delete(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("application history delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def task_list(self, offset = 0, limit = 0, filters = {}):
        result = False
        url = "%s/task/list?offset=%s&limit=%s" % (self.base_url, offset, limit)
        if "task_id" in filters:
            url += "&task_id=%s" % filters["task_id"]
        if "app_id" in filters:
            url += "&app_id=%s" % filters["app_id"]
        if "work_id" in filters:
            url += "&work_id=%s" % filters["work_id"]
        if "name" in filters:
            url += "&name=%s" % urllib.parse.quote(filters["name"])
        if "stage" in filters:
            url += "&stage=%s" % filters["stage"]
        if "status" in filters:
            url += "&status=%s" % filters["status"]
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task list failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def task_info(self, task_id):
        result = False
        url = "%s/task/info?task_id=%s" % (self.base_url, task_id)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def task_delete(self, task_id):
        result = False
        url = "%s/task/delete?task_id=%s" % (self.base_url, task_id)
        r = requests.delete(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def task_create(self, name, app_id, input_data = {}):
        result = False
        url = "%s/task/create" % self.base_url
        data = {"task_name": name, "app_id": app_id, "input_data": input_data}
        r = requests.post(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task create failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def task_rerun(self, task_id):
        result = False
        url = "%s/task/rerun" % self.base_url
        data = {"task_id": task_id}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task rerun failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def task_recover(self, task_id):
        result = False
        url = "%s/task/recover" % self.base_url
        data = {"task_id": task_id}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task recover failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def task_stop(self, task_id, stop_signal):
        result = False
        url = "%s/task/stop" % self.base_url
        data = {"task_id": task_id, "signal": stop_signal}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task stop failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def cluster_info(self, include = ["manager", "nodes", "actions"]):
        result = False
        url = "%s/cluster/info?include=%s" % (self.base_url, ",".join(include))
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("cluster info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def workspace_delete(self, task_id):
        result = False
        url = "%s/workspace/delete" % self.base_url
        data = {"task_ids": task_id}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("workspace delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def workspace_pack(self, task_id, name, force = True, callback = None):
        pack_error = False
        download_ready = False
        url = "%s/workspace/pack" % self.base_url
        if force:
            data = {"task_id": task_id, "name": name, "force": force}
            r = requests.put(url, json = data, headers = self.headers)
            if r.status_code == 200:
                data = r.json()
                if "result" in data and data["result"] == "ok":
                    download_ready = True
                elif "result" in data and data["result"] == "OperationRunning":
                    if callback:
                        callback()
                else:
                    pack_error = True
                    raise OperationFailedError("workspace pack failed: %s" % data["result"])
            else:
                pack_error = True
                raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
            time.sleep(0.5)
        while not pack_error and not download_ready:
            data = {"task_id": task_id, "name": name, "force": False}
            r = requests.put(url, json = data, headers = self.headers)
            if r.status_code == 200:
                data = r.json()
                if "result" in data and data["result"] == "ok":
                    download_ready = True
                elif "result" in data and data["result"] == "OperationRunning":
                    if callback:
                        callback()
                else:
                    pack_error = True
                    raise OperationFailedError("workspace pack failed: %s" % data["result"])
            else:
                pack_error = True
                raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
            time.sleep(0.5)
        return download_ready

    def workspace_download(self, task_id, name, directory = ".", callback = None):
        result = False
        url = "%s/workspace/download?task_id=%s&name=%s" % (self.base_url, task_id, urllib.parse.quote(name))
        with requests.get(url, allow_redirects = True, stream = True, timeout = 3600, headers = self.headers) as r:
            r.raise_for_status()
            file_name = "%s.%s.tar.gz" % (task_id, name)
            file_path = os.path.join(directory, file_name)
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size = 64 * 1024):
                    if chunk:
                        f.write(chunk)
                        if callback:
                            callback()
                result = file_path
        return result

    def workflow_list(self, offset = 0, limit = 0, filters = {}):
        result = False
        url = "%s/workflow/list?offset=%s&limit=%s" % (self.base_url, offset, limit)
        if "workflow_id" in filters:
            url += "&id=%s" % filters["workflow_id"]
        if "name" in filters:
            url += "&name=%s" % urllib.parse.quote(filters["name"])
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("workflow list failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def workflow_info(self, workflow_id):
        result = False
        url = "%s/workflow/info?workflow_id=%s" % (self.base_url, workflow_id)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("workflow info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def workflow_delete(self, workflow_id):
        result = False
        url = "%s/workflow/delete?workflow_id=%s" % (self.base_url, workflow_id)
        r = requests.delete(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("workflow delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def workflow_create(self, name, configuration, description = "", enable = False):
        result = False
        url = "%s/workflow/create" % self.base_url
        data = {
            "name": name,
            "configuration": configuration,
            "description": description,
            "enable": enable,
        }
        r = requests.post(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("workflow create failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def workflow_update(self, workflow_id, name = "", configuration = {}, description = "", enable = None):
        result = False
        url = "%s/workflow/update?workflow_id=%s" % (self.base_url, workflow_id)
        data = {}
        if name:
            data["name"] = name
        if configuration:
            data["configuration"] = configuration
        if description:
            data["description"] = description
        if isinstance(enable, bool):
            data["enable"] = enable
        if data:
            data["workflow_id"] = workflow_id
            r = requests.put(url, json = data, headers = self.headers)
            if r.status_code == 200:
                data = r.json()
                if "result" in data and data["result"] == "ok":
                    result = data
                else:
                    raise OperationFailedError("workflow create failed: %s" % data["result"])
            else:
                raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        else:
            result = True
        return result

    def work_list(self, offset = 0, limit = 0, filters = {}):
        result = False
        url = "%s/work/list?offset=%s&limit=%s" % (self.base_url, offset, limit)
        if "work_id" in filters:
            url += "&work_id=%s" % filters["work_id"]
        if "workflow_id" in filters:
            url += "&workflow_id=%s" % filters["workflow_id"]
        if "name" in filters:
            url += "&name=%s" % urllib.parse.quote(filters["name"])
        if "stage" in filters:
            url += "&stage=%s" % filters["stage"]
        if "status" in filters:
            url += "&status=%s" % filters["status"]
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("work list failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def work_info(self, work_id):
        result = False
        url = "%s/work/info?work_id=%s" % (self.base_url, work_id)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("task info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def work_delete(self, work_id):
        result = False
        url = "%s/work/delete?work_id=%s" % (self.base_url, work_id)
        r = requests.delete(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("work delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def work_create(self, name, workflow_id, input_data = {}):
        result = False
        url = "%s/work/create" % self.base_url
        data = {"name": name, "workflow_id": workflow_id, "input_data": input_data}
        r = requests.post(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("work create failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def work_rerun(self, work_id):
        result = False
        url = "%s/work/rerun" % self.base_url
        data = {"work_id": work_id}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("work rerun failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def work_recover(self, work_id):
        result = False
        url = "%s/work/recover" % self.base_url
        data = {"work_id": work_id}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("work recover failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def work_stop(self, work_id, stop_signal):
        result = False
        url = "%s/work/stop" % self.base_url
        data = {"work_id": work_id, "signal": stop_signal}
        r = requests.put(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("work stop failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def schedule_list(self, offset = 0, limit = 0, filters = {}):
        result = False
        url = "%s/schedule/list?offset=%s&limit=%s" % (self.base_url, offset, limit)
        if "schedule_id" in filters:
            url += "&schedule_id=%s" % filters["schedule_id"]
        if "app_id" in filters:
            url += "&source_id=%s" % filters["app_id"]
        if "workflow_id" in filters:
            url += "&source_id=%s" % filters["workflow_id"]
        if "name" in filters:
            url += "&name=%s" % urllib.parse.quote(filters["name"])
        if "enable" in filters:
            url += "&enable=%s" % filters["enable"]
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("schedule list failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def schedule_info(self, schedule_id):
        result = False
        url = "%s/schedule/info?schedule_id=%s" % (self.base_url, schedule_id)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("schedule info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def schedule_delete(self, schedule_id):
        result = False
        url = "%s/schedule/delete?schedule_id=%s" % (self.base_url, schedule_id)
        r = requests.delete(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("schedule delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def schedule_create(self, name, source, source_id, input_data = {}, minute = -1, hour = -1, day_of_month = -1, day_of_week = -1, enable = False):
        result = False
        url = "%s/schedule/create" % self.base_url
        data = {
            "schedule_name": name,
            "input_data": input_data,
            "source": source,
            "source_id": source_id,
            "minute": minute,
            "hour": hour,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "enable": enable,
        }
        r = requests.post(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("schedule create failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def schedule_update(self, schedule_id, update_data = {}):
        result = False
        url = "%s/schedule/update?schedule_id=%s" % (self.base_url, schedule_id)
        data = {"schedule_id": schedule_id}
        if "name" in update_data:
            data["schedule_name"] = update_data["name"]
        if "source" in update_data:
            data["source"] = update_data["source"]
        if "source_id" in update_data:
            data["source_id"] = update_data["source_id"]
        if "input_data" in update_data:
            data["input_data"] = update_data["input_data"]
        if "minute" in update_data:
            data["minute"] = update_data["minute"]
        if "hour" in update_data:
            data["hour"] = update_data["hour"]
        if "day_of_month" in update_data:
            data["day_of_month"] = update_data["day_of_month"]
        if "day_of_week" in update_data:
            data["day_of_week"] = update_data["day_of_week"]
        if "enable" in update_data:
            data["enable"] = update_data["enable"]
        r = requests.put(url, json = data)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("schedule update failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def service_list(self, offset = 0, limit = 0, filters = {}):
        result = False
        url = "%s/service/list?offset=%s&limit=%s" % (self.base_url, offset, limit)
        if "service_id" in filters:
            url += "&service_id=%s" % filters["service_id"]
        if "app_id" in filters:
            url += "&app_id=%s" % filters["app_id"]
        if "name" in filters:
            url += "&name=%s" % urllib.parse.quote(filters["name"])
        if "enable" in filters:
            url += "&enable=%s" % filters["enable"]
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("service list failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def service_info(self, service_id):
        result = False
        url = "%s/service/info?service_id=%s" % (self.base_url, service_id)
        r = requests.get(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("service info failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def service_delete(self, service_id):
        result = False
        url = "%s/service/delete?service_id=%s" % (self.base_url, service_id)
        r = requests.delete(url, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("service delete failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def service_create(self, name, app_id, description = "", input_data = {}, enable = False):
        result = False
        url = "%s/service/create" % self.base_url
        data = {
            "name": name,
            "app_id": app_id,
            "description": description,
            "input_data": input_data,
            "enable": enable,
        }
        r = requests.post(url, json = data, headers = self.headers)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("service create failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result

    def service_update(self, service_id, update_data = {}):
        result = False
        url = "%s/service/update?service_id=%s" % (self.base_url, service_id)
        data = {"service_id": service_id}
        if "name" in update_data:
            data["name"] = update_data["name"]
        if "app_id" in update_data:
            data["app_id"] = update_data["app_id"]
        if "description" in update_data:
            data["description"] = update_data["description"]
        if "input_data" in update_data:
            data["input_data"] = update_data["input_data"]
        if "enable" in update_data:
            data["enable"] = update_data["enable"]
        r = requests.put(url, json = data)
        if r.status_code == 200:
            data = r.json()
            if "result" in data and data["result"] == "ok":
                result = data
            else:
                raise OperationFailedError("service update failed: %s" % data["result"])
        else:
            raise OperationFailedError("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
        return result
