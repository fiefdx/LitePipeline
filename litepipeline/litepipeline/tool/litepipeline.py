#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import re
import sys
import json
import time
import urllib
import argparse

import requests
from progress.spinner import Spinner
from litepipeline_helper.models.client import LitePipelineClient

from litepipeline.version import __version__

parser = argparse.ArgumentParser(prog = 'litepipeline')

# common arguments
parser.add_argument("address", help = "manager address, host:port")
parser.add_argument("-W", "--column_width", help = "column max width", type = int, default = 0)
parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)
subparsers = parser.add_subparsers(dest = "object", help = 'sub-command help')

# operate with application
parser_app = subparsers.add_parser("app", help = "operate with app API")
subparsers_app = parser_app.add_subparsers(dest = "operation", help = 'sub-command app help')

parser_app_create = subparsers_app.add_parser("create", help = "create application")
parser_app_create.add_argument("-f", "--file", required = True, help = "application's file", default = "")
parser_app_create.add_argument("-n", "--name", required = True, help = "application's name", default = "")
parser_app_create.add_argument("-d", "--description", help = "application's description", default = "")
parser_app_create.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_delete = subparsers_app.add_parser("delete", help = "delete application")
parser_app_delete.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_update = subparsers_app.add_parser("update", help = "update application")
parser_app_update.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_update.add_argument("-f", "--file", help = "application's file", default = "")
parser_app_update.add_argument("-n", "--name", help = "application's name", default = "")
parser_app_update.add_argument("-d", "--description", help = "application's description", default = "")
parser_app_update.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_list = subparsers_app.add_parser("list", help = "list applications")
parser_app_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_app_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_app_list.add_argument("-a", "--app_id", help = "application id filter", default = "")
parser_app_list.add_argument("-n", "--name", help = "application's name filter: '*actions*'", default = "")
parser_app_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_info = subparsers_app.add_parser("info", help = "application's info")
parser_app_info.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_download = subparsers_app.add_parser("download", help = "download application")
parser_app_download.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_download.add_argument("-s", "--sha1", help = "application sha1", default = "")
parser_app_download.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with application history
parser_app_history = subparsers.add_parser("app_history", help = "operate with app_history API")
subparsers_app_history = parser_app_history.add_subparsers(dest = "operation", help = 'sub-command app_history help')

parser_app_history_delete = subparsers_app_history.add_parser("delete", help = "delete application history")
parser_app_history_delete.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_history_delete.add_argument("-H", "--history_id", required = True, help = "history id", default = "")
parser_app_history_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_history_activate = subparsers_app_history.add_parser("activate", help = "activate application history")
parser_app_history_activate.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_history_activate.add_argument("-H", "--history_id", required = True, help = "history id", default = "")
parser_app_history_activate.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_history_list = subparsers_app_history.add_parser("list", help = "list application histories")
parser_app_history_list.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_history_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_app_history_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_app_history_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_history_info = subparsers_app_history.add_parser("info", help = "application history's info")
parser_app_history_info.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_history_info.add_argument("-H", "--history_id", required = True, help = "history id", default = "")
parser_app_history_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with task
parser_task = subparsers.add_parser("task", help = "operate with task API")
subparsers_task = parser_task.add_subparsers(dest = "operation", help = 'sub-command task help')

parser_task_create = subparsers_task.add_parser("create", help = "create task")
parser_task_create.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_task_create.add_argument("-n", "--name", required = True, help = "task's name", default = "")
parser_task_create.add_argument("-i", "--input", help = "task's input data, json string", default = "{}")
parser_task_create.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_task_delete = subparsers_task.add_parser("delete", help = "delete task")
parser_task_delete.add_argument("-t", "--task_id", required = True, help = "task id", default = "")
parser_task_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_task_list = subparsers_task.add_parser("list", help = "list tasks")
parser_task_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_task_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_task_list.add_argument("-t", "--task_id", help = "task id filter", default = "")
parser_task_list.add_argument("-a", "--app_id", help = "application id filter", default = "")
parser_task_list.add_argument("-w", "--work_id", help = "work id filter", default = "")
parser_task_list.add_argument("-n", "--name", help = "task's name filter: '*actions*'", default = "")
parser_task_list.add_argument("-s", "--stage", choices = ["pending", "running", "finished"], help = "task's executing stage", default = "")
parser_task_list.add_argument("-S", "--status", choices = ["success", "fail", "kill", "cancel", "terminate", "error"], help = "task's executing status", default = "")
parser_task_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_task_info = subparsers_task.add_parser("info", help = "task's info")
parser_task_info.add_argument("-t", "--task_id", required = True, help = "task id", default = "")
parser_task_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_task_rerun = subparsers_task.add_parser("rerun", help = "rerun task")
parser_task_rerun.add_argument("-t", "--task_id", required = True, help = "task id", default = "")
parser_task_rerun.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_task_recover = subparsers_task.add_parser("recover", help = "recover task")
parser_task_recover.add_argument("-t", "--task_id", required = True, help = "task id", default = "")
parser_task_recover.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_task_stop = subparsers_task.add_parser("stop", help = "stop task")
parser_task_stop.add_argument("-t", "--task_id", required = True, help = "task id", default = "")
parser_task_stop.add_argument("-g", "--signal", help = "stop task's signal: -9 or -15, default is -9", type = int, default = -9)
parser_task_stop.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with cluster
parser_cluster = subparsers.add_parser("cluster", help = "operate with cluster API")
subparsers_cluster = parser_cluster.add_subparsers(dest = "operation", help = 'sub-command cluster help')

parser_cluster_info = subparsers_cluster.add_parser("info", help = "cluster's info")
parser_cluster_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with workspace
parser_workspace = subparsers.add_parser("workspace", help = "operate with workspace API")
subparsers_workspace = parser_workspace.add_subparsers(dest = "operation", help = 'sub-command workspace help')

parser_workspace_delete = subparsers_workspace.add_parser("delete", help = "delete workspace")
parser_workspace_delete.add_argument("-t", "--task_id", required = True, help = "task id", action = "append")
parser_workspace_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_workspace_download = subparsers_workspace.add_parser("download", help = "download workspace")
parser_workspace_download.add_argument("-t", "--task_id", required = True, help = "task id", default = "")
parser_workspace_download.add_argument("-n", "--name", required = True, help = "action name", default = "")
parser_workspace_download.add_argument("-f", "--force", help = "force repack workspace", action = "store_true")
parser_workspace_download.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with workflow
parser_workflow = subparsers.add_parser("workflow", help = "operate with workflow API")
subparsers_workflow = parser_workflow.add_subparsers(dest = "operation", help = 'sub-command workflow help')

parser_workflow_create = subparsers_workflow.add_parser("create", help = "create workflow")
parser_workflow_create.add_argument("-n", "--name", required = True, help = "workflow's name", default = "")
parser_workflow_create.add_argument("-c", "--config", help = "workflow's json configuration file", default = "")
parser_workflow_create.add_argument("-d", "--description", help = "workflow's description", default = "")
parser_workflow_create.add_argument("-e", "--enable", choices = ["true", "false"], help = "workflow's enable flag", default = "false")
parser_workflow_create.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_workflow_delete = subparsers_workflow.add_parser("delete", help = "delete workflow")
parser_workflow_delete.add_argument("-w", "--workflow_id", required = True, help = "workflow id", default = "")
parser_workflow_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_workflow_update = subparsers_workflow.add_parser("update", help = "update workflow")
parser_workflow_update.add_argument("-w", "--workflow_id", required = True, help = "workflow id", default = "")
parser_workflow_update.add_argument("-n", "--name", help = "workflow's name", default = "")
parser_workflow_update.add_argument("-c", "--config", help = "workflow's json configuration file", default = "")
parser_workflow_update.add_argument("-d", "--description", help = "workflow's description", default = "")
parser_workflow_update.add_argument("-e", "--enable", choices = ["true", "false"], help = "workflow's enable flag", default = "false")
parser_workflow_update.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_workflow_list = subparsers_workflow.add_parser("list", help = "list workflow")
parser_workflow_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_workflow_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_workflow_list.add_argument("-w", "--workflow_id", help = "workflow id filter", default = "")
parser_workflow_list.add_argument("-n", "--name", help = "workflow's name filter: '*actions*'", default = "")
parser_workflow_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_workflow_info = subparsers_workflow.add_parser("info", help = "workflow's info")
parser_workflow_info.add_argument("-w", "--workflow_id", required = True, help = "workflow id", default = "")
parser_workflow_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with work
parser_work = subparsers.add_parser("work", help = "operate with work API")
subparsers_work = parser_work.add_subparsers(dest = "operation", help = 'sub-command work help')

parser_work_create = subparsers_work.add_parser("create", help = "create work")
parser_work_create.add_argument("-w", "--workflow_id", required = True, help = "workflow id", default = "")
parser_work_create.add_argument("-n", "--name", required = True, help = "work's name", default = "")
parser_work_create.add_argument("-i", "--input", help = "work's input data, json string", default = "{}")
parser_work_create.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_work_delete = subparsers_work.add_parser("delete", help = "delete work")
parser_work_delete.add_argument("-w", "--work_id", required = True, help = "work id", default = "")
parser_work_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_work_list = subparsers_work.add_parser("list", help = "list works")
parser_work_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_work_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_work_list.add_argument("-w", "--work_id", help = "work id filter", default = "")
parser_work_list.add_argument("-W", "--workflow_id", help = "workflow id filter", default = "")
parser_work_list.add_argument("-n", "--name", help = "work's name filter: '*actions*'", default = "")
parser_work_list.add_argument("-s", "--stage", choices = ["pending", "running", "finished"], help = "task's executing stage", default = "")
parser_work_list.add_argument("-S", "--status", choices = ["success", "fail", "kill", "cancel", "terminate", "error"], help = "task's executing status", default = "")
parser_work_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_work_info = subparsers_work.add_parser("info", help = "work's info")
parser_work_info.add_argument("-w", "--work_id", required = True, help = "work id", default = "")
parser_work_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_work_rerun = subparsers_work.add_parser("rerun", help = "rerun work")
parser_work_rerun.add_argument("-w", "--work_id", required = True, help = "work id", default = "")
parser_work_rerun.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_work_recover = subparsers_work.add_parser("recover", help = "recover work")
parser_work_recover.add_argument("-w", "--work_id", required = True, help = "work id", default = "")
parser_work_recover.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_work_stop = subparsers_work.add_parser("stop", help = "stop work")
parser_work_stop.add_argument("-w", "--work_id", required = True, help = "work id", default = "")
parser_work_stop.add_argument("-g", "--signal", help = "stop work's signal: -9 or -15, default is -9", type = int, default = -9)
parser_work_stop.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with schedule
parser_schedule = subparsers.add_parser("schedule", help = "operate with schedule API")
subparsers_schedule = parser_schedule.add_subparsers(dest = "operation", help = 'sub-command schedule help')

parser_schedule_create = subparsers_schedule.add_parser("create", help = "create schedule")
parser_schedule_create.add_argument("-a", "--app_id", help = "application id", default = "")
parser_schedule_create.add_argument("-w", "--workflow_id", help = "workflow id", default = "")
parser_schedule_create.add_argument("-n", "--name", required = True, help = "schedule's name", default = "")
parser_schedule_create.add_argument("-i", "--input", help = "task's input data, json string", default = "{}")
parser_schedule_create.add_argument("-m", "--minute", help = "minute, [0, 59]", type = int, default = -1)
parser_schedule_create.add_argument("-H", "--hour", help = "hour, [0, 23]", type = int, default = -1)
parser_schedule_create.add_argument("-d", "--day_of_month", help = "day of month, [1, 31]", type = int, default = -1)
parser_schedule_create.add_argument("-D", "--day_of_week", help = "day of week, [0, 6] (Sunday = 0)", type = int, default = -1)
parser_schedule_create.add_argument("-e", "--enable", choices = ["true", "false"], help = "schedule's enable flag", default = "false")
parser_schedule_create.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_schedule_update = subparsers_schedule.add_parser("update", help = "update schedule")
parser_schedule_update.add_argument("-s", "--schedule_id", required = True, help = "schedule id", default = "")
parser_schedule_update.add_argument("-a", "--app_id", help = "application id")
parser_schedule_update.add_argument("-w", "--workflow_id", help = "workflow id")
parser_schedule_update.add_argument("-n", "--name", help = "schedule's name")
parser_schedule_update.add_argument("-i", "--input", help = "task's input data, json string")
parser_schedule_update.add_argument("-m", "--minute", help = "minute, [0, 59]", type = int)
parser_schedule_update.add_argument("-H", "--hour", help = "hour, [0, 23]", type = int)
parser_schedule_update.add_argument("-d", "--day_of_month", help = "day of month, [1, 31]", type = int)
parser_schedule_update.add_argument("-D", "--day_of_week", help = "day of week, [0, 6] (Sunday = 0)", type = int)
parser_schedule_update.add_argument("-e", "--enable", choices = ["true", "false"], help = "schedule's enable flag")
parser_schedule_update.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_schedule_delete = subparsers_schedule.add_parser("delete", help = "delete schedule")
parser_schedule_delete.add_argument("-s", "--schedule_id", required = True, help = "schedule id", default = "")
parser_schedule_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_schedule_list = subparsers_schedule.add_parser("list", help = "list schedules")
parser_schedule_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_schedule_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_schedule_list.add_argument("-s", "--schedule_id", help = "schedule id filter", default = "")
parser_schedule_list.add_argument("-a", "--app_id", help = "application id filter", default = "")
parser_schedule_list.add_argument("-w", "--workflow_id", help = "workflow id filter", default = "")
parser_schedule_list.add_argument("-n", "--name", help = "schedule's name filter: '*actions*'", default = "")
parser_schedule_list.add_argument("-e", "--enable", choices = ["true", "false"], help = "schedule's enable flag", default = "")
parser_schedule_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_schedule_info = subparsers_schedule.add_parser("info", help = "schedule's info")
parser_schedule_info.add_argument("-s", "--schedule_id", required = True, help = "schedule id", default = "")
parser_schedule_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

# operate with service
parser_service = subparsers.add_parser("service", help = "operate with service API")
subparsers_service = parser_service.add_subparsers(dest = "operation", help = 'sub-command service help')

parser_service_create = subparsers_service.add_parser("create", help = "create service")
parser_service_create.add_argument("-n", "--name", required = True, help = "service_id's name", default = "")
parser_service_create.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_service_create.add_argument("-i", "--input", help = "task's input data, json string", default = "{}")
parser_service_create.add_argument("-d", "--description", help = "service's description", default = "")
parser_service_create.add_argument("-e", "--enable", choices = ["true", "false"], help = "service's enable flag", default = "false")
parser_service_create.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_service_update = subparsers_service.add_parser("update", help = "update service")
parser_service_update.add_argument("-s", "--service_id", required = True, help = "service id", default = "")
parser_service_update.add_argument("-a", "--app_id", help = "application id")
parser_service_update.add_argument("-n", "--name", help = "service's name")
parser_service_update.add_argument("-i", "--input", help = "task's input data, json string")
parser_service_update.add_argument("-d", "--description", help = "service's description")
parser_service_update.add_argument("-e", "--enable", choices = ["true", "false"], help = "service's enable flag")
parser_service_update.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_service_delete = subparsers_service.add_parser("delete", help = "delete service")
parser_service_delete.add_argument("-s", "--service_id", required = True, help = "service id", default = "")
parser_service_delete.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_service_list = subparsers_service.add_parser("list", help = "list services")
parser_service_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_service_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_service_list.add_argument("-s", "--service_id", help = "service id filter", default = "")
parser_service_list.add_argument("-a", "--app_id", help = "application id filter", default = "")
parser_service_list.add_argument("-n", "--name", help = "service's name filter: '*service*'", default = "")
parser_service_list.add_argument("-e", "--enable", choices = ["true", "false"], help = "service's enable flag", default = "")
parser_service_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_service_info = subparsers_service.add_parser("info", help = "service's info")
parser_service_info.add_argument("-s", "--service_id", required = True, help = "service_id id", default = "")
parser_service_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

args = parser.parse_args()


def print_table_result(data, fields):
    fields.insert(0, "#")
    field_length_map = {}
    lines = []
    num = 1
    column_max_width = args.column_width
    for field in fields:
        field_length_map[field] = len(field)
    for item in data:
        line = []
        for field in fields:
            if field == "#":
                line.append(str(num))
            else:
                v = str(item[field]) if field in item else ""
                v_len = len(v)
                if column_max_width > 0 and v_len > column_max_width:
                    v_len = column_max_width
                    v = v[:v_len]
                if v_len > field_length_map[field]:
                    field_length_map[field] = v_len
                line.append(v)
        lines.append(tuple(line))
        num += 1
    field_length_map["#"] = len(str(num))
    format_str = ""
    for field in fields:
        field_len = field_length_map[field]
        if field == "#":
            format_str += "%" + " %s" % field_len + "s | "
        else:
            format_str += "%" + "-%s" % field_len + "s | "
    format_str = format_str[:-3]
    print(format_str % tuple(fields))
    for line in lines:
        print(format_str % line)


def main():
    try:
        address = args.address
        object = args.object
        operation = args.operation
        raw = args.raw
        url = "http://%s/%s/%s" % (address, object, operation)
        if address:
            host, port = address.split(":")
            lpl = LitePipelineClient(host, port)
            if object == "app":
                if operation == "list":
                    try:
                        filters = {}
                        if args.name:
                            filters["name"] = args.name
                        if args.app_id:
                            filters["id"] = args.app_id
                        data = lpl.application_list(args.offset, args.limit, filters)
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    data["apps"],
                                    [
                                        "application_id",
                                        "name",
                                        "create_at",
                                        "update_at",
                                    ]
                                )
                    except Exception as e:
                        print(e)
                elif operation == "info":
                    if args.app_id:
                        try:
                            data = lpl.application_info(args.app_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data["app_info"]],
                                        [
                                            "application_id",
                                            "name",
                                            "create_at",
                                            "update_at",
                                            "sha1",
                                            "description",
                                        ]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.app_id:
                        try:
                            data = lpl.application_delete(args.app_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.file and args.name:
                        try:
                            data = lpl.application_create(args.file, args.name, args.description)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["app_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "update":
                    if args.app_id:
                        try:
                            data = lpl.application_update(args.app_id, args.file, args.name, args.description)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["app_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        print("error: need app_id(-a, --app_id) parameter")
                elif operation == "download":
                    if args.app_id:
                        try:
                            data = lpl.application_download(args.app_id, sha1 = args.sha1)
                            if data:
                                print("application: %s" % data)
                        except Exception as e:
                            print(e)
                    else:
                        print("error: need app_id(-a, --app_id) parameter")
            elif object == "app_history":
                if operation == "list":
                    try:
                        data = lpl.application_history_list(args.app_id, args.offset, args.limit)
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    data["app_histories"],
                                    [
                                    	"id",
                                        "application_id",
                                        "sha1",
                                        "create_at",
                                    ]
                                )
                    except Exception as e:
                        print(e)
                elif operation == "info":
                    if args.app_id and args.history_id:
                        try:
                            data = lpl.application_history_info(args.app_id, args.history_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data["app_history"]],
                                        [
                                        	"id",
                                            "application_id",
                                            "sha1",
                                            "create_at",
                                            "description",
                                        ]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.app_id and args.history_id:
                        try:
                            data = lpl.application_history_delete(args.app_id, args.history_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "activate":
                    if args.app_id and args.history_id:
                        try:
                            data = lpl.application_history_activate(args.app_id, args.history_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        print("error: need app_id(-a, --app_id) parameter")
            elif object == "task":
                if operation == "list":
                    try:
                        filters = {}
                        if args.task_id:
                            filters["task_id"] = args.task_id
                        if args.app_id:
                            filters["app_id"] = args.app_id
                        if args.work_id:
                            filters["work_id"] = args.work_id
                        if args.name:
                            filters["name"] = args.name
                        if args.stage:
                            filters["stage"] = args.stage
                        if args.status:
                            filters["status"] = args.status
                        data = lpl.task_list(args.offset, args.limit, filters)
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    data["tasks"],
                                    [
                                        "task_id",
                                        "application_id",
                                        "task_name",
                                        "create_at",
                                        "start_at",
                                        "end_at",
                                        "stage",
                                        "status",
                                    ]
                                )
                    except Exception as e:
                        print(e)
                elif operation == "info":
                    if args.task_id:
                        try:
                            data = lpl.task_info(args.task_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data["task_info"]],
                                        [
                                            "task_id",
                                            "application_id",
                                            "task_name",
                                            "create_at",
                                            "start_at",
                                            "end_at",
                                            "stage",
                                            "status",
                                        ]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.task_id:
                        try:
                            data = lpl.task_delete(args.task_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.name and args.app_id and args.input:
                        try:
                            data = lpl.task_create(args.name, args.app_id, json.loads(args.input))
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["task_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "rerun":
                    if args.task_id:
                        try:
                            data = lpl.task_rerun(args.task_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "recover":
                    if args.task_id:
                        try:
                            data = lpl.task_recover(args.task_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "stop":
                    if args.task_id and args.signal:
                        try:
                            data = lpl.task_stop(args.task_id, args.signal)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
            elif object == "cluster":
                if operation == "info":
                    try:
                        data = lpl.cluster_info()
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    [data["info"]["manager"]],
                                    [
                                        "http_host",
                                        "http_port",
                                        "tcp_host",
                                        "tcp_port",
                                        "ldfs_http_host",
                                        "ldfs_http_port",
                                        "version",
                                        "data_path",
                                    ]
                                )
                                print()
                                print_table_result(
                                    data["info"]["nodes"],
                                    [
                                        "node_id",
                                        "http_host",
                                        "http_port",
                                        "action_slots",
                                        "version",
                                        "data_path",
                                    ]
                                )
                    except Exception as e:
                        print(e)
            elif object == "workspace":
                if operation == "delete":
                    if args.task_id:
                        try:
                            data = lpl.workspace_delete(args.task_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "download":
                    if args.task_id and args.name:
                        try:
                            spinner = Spinner('Packing ... ')
                            download_ready = lpl.workspace_pack(args.task_id, args.name, force = args.force, callback = spinner.next)
                            if download_ready:
                                print()
                                spinner = Spinner('Downloading ... ')
                                file_path = lpl.workspace_download(args.task_id, args.name, callback = spinner.next)
                                if file_path:
                                    print("\nWorkspace: %s" % file_path)
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
            elif object == "workflow":
                if operation == "list":
                    try:
                        filters = {}
                        if args.name:
                            filters["name"] = args.name
                        if args.workflow_id:
                            filters["id"] = args.workflow_id
                        data = lpl.workflow_list(args.offset, args.limit, filters)
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    data["workflows"],
                                    [
                                        "workflow_id",
                                        "name",
                                        "create_at",
                                        "update_at",
                                        "enable",
                                    ]
                                )
                    except Exception as e:
                        print(e)
                elif operation == "info":
                    if args.workflow_id:
                        try:
                            data = lpl.workflow_info(args.workflow_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data["info"]],
                                        [
                                            "workflow_id",
                                            "name",
                                            "create_at",
                                            "update_at",
                                            "enable",
                                            "description",
                                        ]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.workflow_id:
                        try:
                            data = lpl.workflow_delete(args.workflow_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.name:
                        try:
                            configuration = {}
                            enable = True if args.enable == "true" else False
                            if args.config and os.path.exists(args.config) and os.path.isfile(args.config):
                                fp = open(args.config, "r")
                                content = fp.read()
                                fp.close()
                                if content:
                                    configuration = json.loads(content)
                            data = lpl.workflow_create(args.name, configuration, args.description, enable)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["workflow_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "update":
                    if args.workflow_id:
                        try:
                            configuration = {}
                            enable = None
                            if args.enable is not None:
                                enable = True if args.enable == "true" else False
                            if args.config and os.path.exists(args.config) and os.path.isfile(args.config):
                                fp = open(args.config, "r")
                                content = fp.read()
                                fp.close()
                                if content:
                                    configuration = json.loads(content)
                            data = lpl.workflow_update(args.workflow_id, args.name, configuration, args.description, enable)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["workflow_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        print("error: need workflow_id(-w, --workflow_id) parameter")
            elif object == "work":
                if operation == "list":
                    try:
                        filters = {}
                        if args.work_id:
                            filters["work_id"] = args.work_id
                        if args.workflow_id:
                            filters["workflow_id"] = args.workflow_id
                        if args.name:
                            filters["name"] = args.name
                        if args.stage:
                            filters["stage"] = args.stage
                        if args.status:
                            filters["status"] = args.status
                        data = lpl.work_list(args.offset, args.limit, filters)
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    data["works"],
                                    [
                                        "work_id",
                                        "workflow_id",
                                        "name",
                                        "create_at",
                                        "start_at",
                                        "end_at",
                                        "stage",
                                        "status",
                                    ]
                                )
                    except Exception as e:
                        print(e)
                elif operation == "info":
                    if args.work_id:
                        try:
                            data = lpl.work_info(args.work_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data["info"]],
                                        [
                                            "work_id",
                                            "workflow_id",
                                            "name",
                                            "create_at",
                                            "start_at",
                                            "end_at",
                                            "stage",
                                            "status",
                                        ]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.work_id:
                        try:
                            data = lpl.work_delete(args.work_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.name and args.workflow_id and args.input:
                        try:
                            data = lpl.work_create(args.name, args.workflow_id, json.loads(args.input))
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["work_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "rerun":
                    if args.work_id:
                        try:
                            data = lpl.work_rerun(args.work_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "recover":
                    if args.work_id:
                        try:
                            data = lpl.work_recover(args.work_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "stop":
                    if args.work_id and args.signal:
                        try:
                            data = lpl.work_stop(args.work_id, args.signal)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
            elif object == "schedule":
                if operation == "list":
                    try:
                        filters = {}
                        if args.schedule_id:
                            filters["schedule_id"] = args.schedule_id
                        if args.app_id:
                            filters["source_id"] = args.app_id
                        if args.workflow_id:
                            filters["source_id"] = args.workflow_id
                        if args.name:
                            filters["name"] = args.name
                        if args.enable:
                            filters["enable"] = args.enable
                        data = lpl.schedule_list(args.offset, args.limit, filters)
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    data["schedules"],
                                    [
                                        "schedule_id",
                                        "source",
                                        "source_id",
                                        "schedule_name",
                                        "create_at",
                                        "update_at",          
                                        "hour",
                                        "minute",
                                        "day_of_month",
                                        "day_of_week",
                                        "enable",
                                    ]
                                )
                    except Exception as e:
                        print(e)
                elif operation == "info":
                    if args.schedule_id:
                        try:
                            data = lpl.schedule_info(args.schedule_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data["schedule_info"]],
                                        [
                                            "schedule_id",
                                            "source",
                                            "source_id",
                                            "schedule_name",
                                            "create_at",
                                            "update_at",
                                            "hour",
                                            "minute",
                                            "day_of_month",
                                            "day_of_week",
                                            "enable",
                                        ]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.schedule_id:
                        try:
                            data = lpl.schedule_delete(args.schedule_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.name and args.input and (args.app_id or args.workflow_id):
                        try:
                            enable = True if args.enable == "true" else False
                            if args.app_id:
                                source = "application"
                                source_id = args.app_id
                            elif args.workflow_id:
                                source = "workflow"
                                source_id = args.workflow_id
                            data = lpl.schedule_create(args.name, source, source_id, json.loads(args.input), args.minute, args.hour, args.day_of_month, args.day_of_week, enable)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["schedule_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "update":
                    if args.schedule_id:
                        try:
                            update_data = {}
                            if args.name is not None:
                                update_data["name"] = args.name
                            if args.app_id is not None:
                                update_data["source"] = "application"
                                update_data["source_id"] = args.app_id
                            elif args.workflow_id is not None:
                                update_data["source"] = "workflow"
                                update_data["source_id"] = args.workflow_id
                            if args.input is not None:
                                update_data["input_data"] = args.input
                            if args.minute is not None:
                                update_data["minute"] = args.minute
                            if args.hour is not None:
                                update_data["hour"] = args.hour
                            if args.day_of_month is not None:
                                update_data["day_of_month"] = args.day_of_month
                            if args.day_of_week is not None:
                                update_data["day_of_week"] = args.day_of_week
                            if args.enable is not None:
                                update_data["enable"] = True if args.enable == "true" else False
                            data = lpl.schedule_update(args.schedule_id, update_data)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["schedule_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
            elif object == "service":
                if operation == "list":
                    try:
                        filters = {}
                        if args.service_id:
                            filters["service_id"] = args.service_id
                        if args.app_id:
                            filters["app_id"] = args.app_id
                        if args.name:
                            filters["name"] = args.name
                        if args.enable:
                            filters["enable"] = args.enable
                        data = lpl.service_list(args.offset, args.limit, filters)
                        if data:
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    data["services"],
                                    [
                                        "service_id",
                                        "name",
                                        "application_id",
                                        "task_id",
                                        "create_at",
                                        "update_at",
                                        "stage",
                                        "status",
                                        "enable",
                                    ]
                                )
                    except Exception as e:
                        print(e)
                elif operation == "info":
                    if args.service_id:
                        try:
                            data = lpl.service_info(args.service_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data["service_info"]],
                                        [
                                            "service_id",
                                            "name",
                                            "application_id",
                                            "task_id",
                                            "create_at",
                                            "update_at",
                                            "stage",
                                            "status",
                                            "enable",
                                        ]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.service_id:
                        try:
                            data = lpl.service_delete(args.service_id)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.name and args.input and args.app_id:
                        try:
                            enable = True if args.enable == "true" else False
                            data = lpl.service_create(args.name, args.app_id, description = args.description, input_data = json.loads(args.input), enable = enable)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["service_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "update":
                    if args.service_id:
                        try:
                            update_data = {}
                            if args.name is not None:
                                update_data["name"] = args.name
                            if args.app_id is not None:
                                update_data["app_id"] = args.app_id
                            if args.input is not None:
                                update_data["input_data"] = args.input
                            if args.description is not None:
                                update_data["description"] = args.description
                            if args.enable is not None:
                                update_data["enable"] = True if args.enable == "true" else False
                            data = lpl.service_update(args.service_id, update_data)
                            if data:
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["service_id", "result", "message"]
                                    )
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
            else:
                parser.print_help()
        else:
            parser.print_help()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
