#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import re
import sys
import json
import time
import argparse

import requests
from progress.spinner import Spinner

from litepipeline.version import __version__

parser = argparse.ArgumentParser(prog = 'litepipeline')

# common arguments
parser.add_argument("address", help = "manager address, host:port")
parser.add_argument("-w", "--column_width", help = "column max width", type = int, default = 0)
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
parser_app_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_info = subparsers_app.add_parser("info", help = "application's info")
parser_app_info.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_app_download = subparsers_app.add_parser("download", help = "download application")
parser_app_download.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_app_download.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

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
parser_task_list.add_argument("-s", "--stage", choices = ["pending", "running", "finished"], help = "task's executing stage", default = "")
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

# operate with schedule
parser_schedule = subparsers.add_parser("schedule", help = "operate with schedule API")
subparsers_schedule = parser_schedule.add_subparsers(dest = "operation", help = 'sub-command schedule help')

parser_schedule_create = subparsers_schedule.add_parser("create", help = "create schedule")
parser_schedule_create.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
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
parser_schedule_list.add_argument("-e", "--enable", choices = ["true", "false"], help = "schedule's enable flag", default = "")
parser_schedule_list.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

parser_schedule_info = subparsers_schedule.add_parser("info", help = "schedule's info")
parser_schedule_info.add_argument("-s", "--schedule_id", required = True, help = "schedule id", default = "")
parser_schedule_info.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")

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
            if object == "app":
                if operation == "list":
                    url += "?offset=%s&limit=%s" % (args.offset, args.limit)
                    r = requests.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        if raw:
                            print(json.dumps(data, indent = 4, sort_keys = True))
                        else:
                            if data["result"] == "ok": 
                                print_table_result(
                                    data["apps"],
                                    [
                                        "application_id",
                                        "name",
                                        "create_at",
                                        "update_at",
                                    ]
                                )
                            else:
                                print_table_result(
                                    [data],
                                    ["result", "message"]
                                )
                    else:
                        print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                elif operation == "info":
                    if args.app_id:
                        url += "?app_id=%s" % args.app_id
                        r = requests.get(url)
                        if r.status_code == 200:
                            data = r.json()
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                if data["result"] == "ok":
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
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.app_id:
                        url += "?app_id=%s" % args.app_id
                        r = requests.delete(url)
                        if r.status_code == 200:
                            data = r.json()
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    [data],
                                    ["result", "message"]
                                )
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.file and args.name:
                        if os.path.exists(args.file) and os.path.isfile(args.file):
                            file_name = os.path.split(args.file)[-1]
                            files = {'up_file': (file_name, open(args.file, "rb"), b"text/plain")}
                            values = {"name": args.name, "description": args.description}
                            r = requests.post(url, files = files, data = values)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["app_id", "result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                        else:
                            print("file[%s] not exists")
                    else:
                        parser.print_help()
                elif operation == "update":
                    if args.app_id:
                        files = {}
                        values = {"app_id": args.app_id}
                        executable = True
                        if args.file:
                            if os.path.exists(args.file) and os.path.isfile(args.file):
                                file_name = os.path.split(args.file)[-1]
                                files = {'up_file': (file_name, open(args.file, "rb"), b"text/plain")}
                            else:
                                print("file[%s] not exists")
                                executable = False
                        if args.name:
                            values["name"] = args.name
                        if args.description:
                            values["description"] = args.description
                        if executable:
                            if files:
                                r = requests.post(url, files = files, data = values)
                            else:
                                for key in values:
                                    values[key] = (None, values[key])
                                r = requests.post(url, files = values)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["app_id", "result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        print("error: need app_id(-a, --app_id) parameter")
                elif operation == "download":
                    if args.app_id:
                        url += "?app_id=%s" % args.app_id
                        file_path = "./%s.tar.gz" % args.app_id
                        r = requests.get(url)
                        if r.status_code == 200:
                            f = open(file_path, 'wb')
                            f.write(r.content)
                            f.close()
                            print("application: %s" % file_path)
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        print("error: need app_id(-a, --app_id) parameter")    
            elif object == "task":
                if operation == "list":
                    url += "?offset=%s&limit=%s" % (args.offset, args.limit)
                    if args.stage:
                        url += "&stage=%s" % args.stage
                    r = requests.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        if raw:
                            print(json.dumps(data, indent = 4, sort_keys = True))
                        else:
                            if data["result"] == "ok":
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
                            else:
                                print_table_result(
                                    [data],
                                    ["result", "message"]
                                )
                    else:
                        print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                elif operation == "info":
                    if args.task_id:
                        url += "?task_id=%s" % args.task_id
                        r = requests.get(url)
                        if r.status_code == 200:
                            data = r.json()
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                if data["result"] == "ok":
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
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.task_id:
                        url += "?task_id=%s" % args.task_id
                        r = requests.delete(url)
                        if r.status_code == 200:
                            data = r.json()
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    [data],
                                    ["result", "message"]
                                )
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.name and args.app_id and args.input:
                        try:
                            data = {"task_name": args.name, "app_id": args.app_id, "input_data": json.loads(args.input)}
                            r = requests.post(url, json = data)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["task_id", "result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "rerun":
                    if args.task_id:
                        try:
                            data = {"task_id": args.task_id}
                            r = requests.put(url, json = data)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "recover":
                    if args.task_id:
                        try:
                            data = {"task_id": args.task_id}
                            r = requests.put(url, json = data)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "stop":
                    if args.task_id and args.signal:
                        try:
                            data = {"task_id": args.task_id, "signal": args.signal}
                            r = requests.put(url, json = data)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
            elif object == "cluster":
                if operation == "info":
                    r = requests.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        if raw:
                            print(json.dumps(data, indent = 4, sort_keys = True))
                        else:
                            if data["result"] == "ok":
                                print_table_result(
                                    data["info"]["nodes"],
                                    [
                                        "node_id",
                                        "http_host",
                                        "http_port",
                                        "action_slots",
                                        "app_path",
                                        "data_path",
                                    ]
                                )
                            else:
                                print_table_result(
                                    [data],
                                    ["result", "message"]
                                )
                    else:
                        print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
            elif object == "workspace":
                if operation == "delete":
                    if args.task_id:
                        try:
                            data = {"task_ids": args.task_id}
                            r = requests.put(url, json = data)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "download":
                    if args.task_id and args.name:
                        pack_error = False
                        download_ready = False
                        try:
                            url = "http://%s/%s/%s" % (address, object, "pack")
                            spinner = Spinner('Packing ... ')
                            if args.force:
                                data = {"task_id": args.task_id, "name": args.name, "force": args.force}
                                r = requests.put(url, json = data)
                                if r.status_code == 200:
                                    data = r.json()
                                    if "result" in data and data["result"] == "ok":
                                        download_ready = True
                                    elif "result" in data and data["result"] == "OperationRunning":
                                        spinner.next()
                                    else:
                                        pack_error = True
                                        if raw:
                                            print(json.dumps(data, indent = 4, sort_keys = True))
                                        else:
                                            print_table_result(
                                                [data],
                                                ["result", "message"]
                                            )
                                else:
                                    pack_error = True
                                    print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                                time.sleep(0.5)
                            while not pack_error and not download_ready:
                                data = {"task_id": args.task_id, "name": args.name, "force": False}
                                r = requests.put(url, json = data)
                                if r.status_code == 200:
                                    data = r.json()
                                    if "result" in data and data["result"] == "ok":
                                        download_ready = True
                                    elif "result" in data and data["result"] == "OperationRunning":
                                        spinner.next()
                                    else:
                                        pack_error = True
                                        if raw:
                                            print(json.dumps(data, indent = 4, sort_keys = True))
                                        else:
                                            print_table_result(
                                                [data],
                                                ["result", "message"]
                                            )
                                else:
                                    pack_error = True
                                    print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                                time.sleep(0.5)
                            url = "http://%s/%s/%s" % (address, object, "download")
                            url += "?task_id=%s&name=%s" % (args.task_id, args.name)
                            print("\nDownload from: %s" % url)
                            spinner = Spinner('Downloading ... ')
                            if not pack_error and download_ready:
                                with requests.get(url, allow_redirects = True, stream = True, timeout = 3600) as r:
                                    r.raise_for_status()
                                    file_name = "%s.%s.tar.gz" % (args.task_id, args.name)
                                    file_path = os.path.join("./", file_name)
                                    with open(file_path, "wb") as f:
                                        for chunk in r.iter_content(chunk_size = 64 * 1024):
                                            if chunk:
                                                f.write(chunk)
                                                spinner.next()
                                    print("\nWorkspace: %s" % file_path)
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
            elif object == "schedule":
                if operation == "list":
                    url += "?offset=%s&limit=%s" % (args.offset, args.limit)
                    if args.enable:
                        url += "&enable=%s" % args.enable
                    r = requests.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        if raw:
                            print(json.dumps(data, indent = 4, sort_keys = True))
                        else:
                            if data["result"] == "ok":
                                print_table_result(
                                    data["schedules"],
                                    [
                                        "schedule_id",
                                        "application_id",
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
                            else:
                                print_table_result(
                                    [data],
                                    ["result", "message"]
                                )
                    else:
                        print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                elif operation == "info":
                    if args.schedule_id:
                        url += "?schedule_id=%s" % args.schedule_id
                        r = requests.get(url)
                        if r.status_code == 200:
                            data = r.json()
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                if data["result"] == "ok":
                                    print_table_result(
                                        [data["schedule_info"]],
                                        [
                                            "schedule_id",
                                            "application_id",
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
                                else:
                                    print_table_result(
                                        [data],
                                        ["result", "message"]
                                    )
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.schedule_id:
                        url += "?schedule_id=%s" % args.schedule_id
                        r = requests.delete(url)
                        if r.status_code == 200:
                            data = r.json()
                            if raw:
                                print(json.dumps(data, indent = 4, sort_keys = True))
                            else:
                                print_table_result(
                                    [data],
                                    ["result", "message"]
                                )
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "create":
                    if args.name and args.app_id and args.input:
                        try:
                            data = {
                                "schedule_name": args.name,
                                "app_id": args.app_id,
                                "input_data": json.loads(args.input),
                                "minute": args.minute,
                                "hour": args.hour,
                                "day_of_month": args.day_of_month,
                                "day_of_week": args.day_of_week,
                                "enable": True if args.enable == "true" else False,
                            }
                            r = requests.post(url, json = data)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["schedule_id", "result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                        except Exception as e:
                            print(e)
                    else:
                        parser.print_help()
                elif operation == "update":
                    if args.schedule_id:
                        try:
                            data = {"schedule_id": args.schedule_id}
                            if args.name is not None:
                                data["schedule_name"] = args.name
                            if args.app_id is not None:
                                data["app_id"] = args.app_id
                            if args.input is not None:
                                data["input_data"] = args.input
                            if args.minute is not None:
                                data["minute"] = args.minute
                            if args.hour is not None:
                                data["hour"] = args.hour
                            if args.day_of_month is not None:
                                data["day_of_month"] = args.day_of_month
                            if args.day_of_week is not None:
                                data["day_of_week"] = args.day_of_week
                            if args.enable is not None:
                                data["enable"] = True if args.enable == "true" else False
                            r = requests.put(url, json = data)
                            if r.status_code == 200:
                                data = r.json()
                                if raw:
                                    print(json.dumps(data, indent = 4, sort_keys = True))
                                else:
                                    print_table_result(
                                        [data],
                                        ["schedule_id", "result", "message"]
                                    )
                            else:
                                print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
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
