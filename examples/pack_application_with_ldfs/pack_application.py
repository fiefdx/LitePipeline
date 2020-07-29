# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import shutil
import logging
import tarfile
import zipfile
import datetime
import subprocess
from pathlib import Path

from litepipeline_helper.models.action import Action
from litedfs_client.client import LiteDFSClient

import logger

LOG = logging.getLogger(__name__)


def splitall(path):
    allparts = []
    while True:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


if __name__ == "__main__":
    workspace, input_data = Action.get_input()

    logs_directory = os.path.join(workspace, "logs")
    logger.config_logging(file_name = "pack_application.log",
                          log_level = "DEBUG",
                          dir_name = logs_directory,
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = False)
    LOG.debug("pack start")
    LOG.debug("input_data: %s", input_data)

    task_name = input_data["action_info"]["task_name"]
    action_name = input_data["action_info"]["action_name"]
    task_id = input_data["task_id"]

    ldfs_host = input_data["ldfs_host"] if "ldfs_host" in input_data and input_data["ldfs_host"] else None
    ldfs_port = input_data["ldfs_port"] if "ldfs_port" in input_data and input_data["ldfs_port"] else None
    
    data = {}
    if ldfs_host and ldfs_port:
        ldfs = LiteDFSClient(ldfs_host, ldfs_port)

        source_app_path = input_data["source"]
        target_app_path = input_data["target"]
        target_app_log_path = target_app_path + ".txt"

        source_format = "tar.gz"
        if "zip" in os.path.split(source_app_path)[-1]:
            source_format = "zip"
        target_format = "tar.gz"
        if "format" in input_data and input_data["format"]:
            target_format = input_data["format"]
        local_tmp_path = os.path.join(workspace, "app.%s" % source_format)
        if os.path.exists(local_tmp_path):
            os.remove(local_tmp_path)
            LOG.info("remove old: %s", local_tmp_path)
        success = ldfs.download_file(source_app_path, local_tmp_path)

        if success:
            if source_format == "zip":
                z = zipfile.ZipFile(local_tmp_path, "r")
                
                path_parts = splitall(z.namelist()[0])
                app_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                local_tmp_app_path = os.path.join(workspace, app_root_name)
                if os.path.exists(local_tmp_app_path):
                    shutil.rmtree(local_tmp_app_path)
                    LOG.info("remove old: %s", local_tmp_app_path)

                z.extractall(workspace)
                z.close()
            else:
                t = tarfile.open(local_tmp_path, "r")
                
                path_parts = splitall(t.getnames()[0])
                app_root_name = path_parts[1] if path_parts[0] == "." else path_parts[0]
                local_tmp_app_path = os.path.join(workspace, app_root_name)
                if os.path.exists(local_tmp_app_path):
                    shutil.rmtree(local_tmp_app_path)
                    LOG.info("remove old: %s", local_tmp_app_path)

                t.extractall(workspace)
                t.close()

            # pack application
            cmd = "cd '%s' && bash './%s/pack.sh %s'" % (workspace, app_root_name, target_format)
            LOG.info("cmd: %s", cmd)
            stdout_file_path = os.path.join(workspace, "stdout.pack.data")
            stdout_file = open(stdout_file_path, "w")
            p = subprocess.Popen(cmd, shell = True, executable = '/bin/bash', bufsize = -1, stdout = stdout_file, stderr = subprocess.STDOUT)
            while p.poll() is None:
                time.sleep(1)
            returncode = p.poll()
            stdout_file.close()
            if returncode == 0:
                packed_tmp_app_path = os.path.join(workspace, "%s.%s" % (app_root_name, target_format))
                ldfs.delete_file(target_app_log_path)
                success = ldfs.create_file(stdout_file_path, target_app_log_path, replica = 1)
                if success:
                    data["app_log_path"] = target_app_log_path
                ldfs.delete_file(target_app_path)
                success = ldfs.create_file(packed_tmp_app_path, target_app_path, replica = 1)
                if success:
                    data["app_path"] = target_app_path
                else:
                    data["message"] = "upload file [%s] failed" % target_app_path
            else:
                data["message"] = "pack failed, returncode: %s" % returncode
        else:
            data["message"] = "download file [%s] failed" % source_app_path
    else:
        data["message"] = "need litedfs configurations"

    Action.set_output(data = data)
    LOG.debug("pack end")
