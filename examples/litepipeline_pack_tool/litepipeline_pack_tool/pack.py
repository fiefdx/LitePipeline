#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import json
import time
import logging
import tarfile
import datetime
import argparse
from pathlib import Path

from litepipeline_helper.models.client import LitePipelineClient
from litedfs_client.client import LiteDFSClient

from litepipeline_pack_tool.version import __version__
from litepipeline_pack_tool import logger

LOG = logging.getLogger(__name__)

parser = argparse.ArgumentParser(prog = 'litepack')

# common arguments
parser.add_argument("-P", "--litepipeline", required = True, help = "litepipeline manager node's host:port")
parser.add_argument("-D", "--litedfs", required = True, help = "litedfs name node's host:port")
parser.add_argument("-p", "--pack_app_id", required = True, help = "pack application id")
parser.add_argument("-o", "--operate", required = True, choices = ["pack", "create", "update"], help = "task's executing stage", default = "pack")
parser.add_argument("-a", "--app_id", help = "application's id, which application will be updated", default = "")
parser.add_argument("-i", "--input", required = True, help = "local application's source code root directory")
parser.add_argument("-n", "--name", help = "application's name", default = "")
parser.add_argument("-d", "--description", help = "application's description", default = "")
parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)

args = parser.parse_args()


def main():
    logger.config_logging(log_level = "DEBUG", console = True, filesystem = False)
    try:
        lpl_address = args.litepipeline
        lpl_host, lpl_port = lpl_address.split(":")
        ldfs_address = args.litedfs
        ldfs_host, ldfs_port = ldfs_address.split(":")

        lpl = LitePipelineClient(lpl_host, lpl_port)
        ldfs = LiteDFSClient(ldfs_host, ldfs_port)
        pack_app_id = args.pack_app_id
        operate = args.operate
        app_path = args.input
        app_id = args.app_id
        app_name = args.name
        app_description = args.description
        workspace = "."

        now = datetime.datetime.now()
        LOG.info("workspace directory: %s, now: %s", workspace, str(now))

        if operate in ["pack", "create", "update"]:
            if os.path.exists(app_path) and os.path.isdir(app_path):
                app_dir_name = os.path.split(app_path.strip("/"))[-1]
                tar_name = "%s.tar.gz" % app_dir_name
                tmp_tar_path = os.path.join(workspace, tar_name)
                if os.path.exists(tmp_tar_path):
                    os.remove(tmp_tar_path)
                    LOG.warning("remove old file [%s]", tmp_tar_path)
                LOG.info("compress [%s] start", tmp_tar_path)
                with tarfile.open(tmp_tar_path, "w:gz") as tar:
                    tar.add(app_path, arcname = app_dir_name)
                LOG.info("compress [%s] end", tmp_tar_path)

                remote_source_path = os.path.join("/pack_application/source", str(now), tar_name)
                ldfs.delete_file(remote_source_path)
                success = ldfs.create_file(tmp_tar_path, remote_source_path, replica = 1)
                if success:
                    LOG.info("upload [%s] to remote [%s] success", tmp_tar_path, remote_source_path)
                    remote_target_path = os.path.join("/pack_application/target", str(now), tar_name)
                    task_name = "pack %s" % app_dir_name
                    task_input = {
                        "source": remote_source_path,
                        "target": remote_target_path,
                    }
                    r = lpl.task_create(task_name, pack_app_id, task_input)
                    if r:
                        task_id = r["task_id"]
                        LOG.info("create pack task [task_id: %s] success", task_id)

                        stage = "running"
                        task_info = None
                        while stage != "finished":
                            task_info = lpl.task_info(task_id)
                            if task_info:
                                stage = task_info["task_info"]["stage"]
                                update_at = task_info["task_info"]["update_at"]
                                LOG.info("task[task_id: %s], stage: %s, update_at: %s", task_id, stage, update_at)
                            time.sleep(5)
                        if task_info:
                            if task_info["task_info"]["status"] == "success":
                                task_result = task_info["task_info"]["result"]["pack application"]["result"]["data"]
                                remote_pack_log_path = task_result["app_log_path"]
                                remote_pack_path = task_result["app_path"]
                                LOG.info("pack task success, remote pack log: %s, remote packed application: %s", remote_pack_log_path, remote_pack_path)
                                
                                local_pack_log_path = os.path.join(workspace, "%s.pack.log" % app_dir_name)
                                local_pack_path = os.path.join(workspace, "%s.pack.tar.gz" % app_dir_name)
                                
                                if os.path.exists(local_pack_log_path) and os.path.isfile(local_pack_log_path):
                                    os.remove(local_pack_log_path)
                                if os.path.exists(local_pack_path) and os.path.isfile(local_pack_path):
                                    os.remove(local_pack_path)

                                success = ldfs.download_file(remote_pack_log_path, local_pack_log_path)
                                if success:
                                    LOG.info("download pack log as [%s] success", local_pack_log_path)
                                else:
                                    LOG.error("download pack log failed")
                                success = ldfs.download_file(remote_pack_path, local_pack_path)
                                if success:
                                    LOG.info("download packed application as [%s] success", local_pack_path)
                                else:
                                    LOG.error("download packed application failed")
                                if operate == "create":
                                    if app_name:
                                        r = lpl.application_create(local_pack_path, app_name, description = app_description)
                                        if r:
                                            LOG.info("create application[app_id: %s] success", r["app_id"])
                                        else:
                                            LOG.error("create application failed")
                                    else:
                                        LOG.error("need -n/--name parameter")
                                elif operate == "update":
                                    if app_id:
                                        r = lpl.application_update(app_id, file_path = local_pack_path)
                                        if r:
                                            LOG.info("update application[app_id: %s] success", r["app_id"])
                                        else:
                                            LOG.error("update application failed")
                                    else:
                                        LOG.error("need -a/--app_id parameter")
                            else:
                                LOG.error("pack task failed\ntask_info: %s", json.dumps(task_info, indent = 4))
                        else:
                            LOG.error("pack task failed")
                    else:
                        LOG.error("create pack task failed")
                else:
                    LOG.error("upload [%s] to remote [%s] failed", tmp_tar_path, remote_source_path)
            else:
                LOG.error("input [%s] directory not exists", app_path)
        else:
            LOG.error("unknown operate: %s", operate)
    except Exception as e:
        LOG.exception(e)


if __name__ == "__main__":
    main()
