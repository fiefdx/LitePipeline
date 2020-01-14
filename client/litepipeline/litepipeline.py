#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import json
import argparse

import requests

parser = argparse.ArgumentParser(prog = 'litepipeline')

# common arguments
parser.add_argument("address", help = "manager address, host:port")
parser.add_argument("-r", "--raw", help = "display raw json data", action = "store_true")
parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s 0.0.3')
subparsers = parser.add_subparsers(dest = "object", help = 'sub-command help')

# operate with application
parser_app = subparsers.add_parser("app", help = "operate with app API")
subparsers_app = parser_app.add_subparsers(dest = "operation", help = 'sub-command app help')

parser_app_create = subparsers_app.add_parser("create", help = "create application")
parser_app_create.add_argument("-f", "--file", required = True, help = "application's file", default = "")
parser_app_create.add_argument("-n", "--name", required = True, help = "application's name", default = "")
parser_app_create.add_argument("-d", "--description", help = "application's description", default = "")

parser_app_delete = subparsers_app.add_parser("delete", help = "delete application")
parser_app_delete.add_argument("-a", "--app_id", required = True, help = "application id", default = "")

parser_app_update = subparsers_app.add_parser("update", help = "update application")
parser_app_update.add_argument("-f", "--file", help = "application's file", default = "")
parser_app_update.add_argument("-n", "--name", help = "application's name", default = "")
parser_app_update.add_argument("-d", "--description", help = "application's description", default = "")

parser_app_list = subparsers_app.add_parser("list", help = "list applications")
parser_app_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_app_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)

parser_app_info = subparsers_app.add_parser("info", help = "application's info")
parser_app_info.add_argument("-a", "--app_id", required = True, help = "application id", default = "")

parser_app_download = subparsers_app.add_parser("download", help = "download application")
parser_app_download.add_argument("-a", "--app_id", required = True, help = "application id", default = "")

# operate with task
parser_task = subparsers.add_parser("task", help = "operate with task API")
subparsers_task = parser_task.add_subparsers(dest = "operation", help = 'sub-command task help')

parser_task_create = subparsers_task.add_parser("create", help = "create task")
parser_task_create.add_argument("-a", "--app_id", required = True, help = "application id", default = "")
parser_task_create.add_argument("-n", "--name", required = True, help = "task's name", default = "")
parser_task_create.add_argument("-i", "--input", help = "task's input data, json string", default = "{}")

parser_task_delete = subparsers_task.add_parser("delete", help = "delete task")
parser_task_delete.add_argument("-t", "--task_id", required = True, help = "task id", default = "")

parser_task_list = subparsers_task.add_parser("list", help = "list tasks")
parser_task_list.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser_task_list.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser_task_list.add_argument("-s", "--stage", choices = ["pending", "running", "finished"], help = "task's executing stage", default = "")

parser_task_info = subparsers_task.add_parser("info", help = "task's info")
parser_task_info.add_argument("-t", "--task_id", required = True, help = "task id", default = "")

parser_task_stop = subparsers_task.add_parser("stop", help = "stop task")
parser_task_stop.add_argument("-t", "--task_id", required = True, help = "task id", default = "")
parser_task_stop.add_argument("-g", "--signal", help = "stop task's signal: -9 or -15", type = int, default = -15)

# operate with cluster
parser_cluster = subparsers.add_parser("cluster", help = "operate with cluster API")
subparsers_cluster = parser_cluster.add_subparsers(dest = "operation", help = 'sub-command cluster help')

parser_cluster_info = subparsers_cluster.add_parser("info", help = "cluster's info")

args = parser.parse_args()


def main():
    try:
        print("*" * 10 + " litepipeline command line tool " + "*" * 10)
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
                        print(json.dumps(r.json(), indent = 4, sort_keys = True))
                    else:
                        print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                elif operation == "info":
                    if args.app_id:
                        url += "?app_id=%s" % args.app_id
                        r = requests.get(url)
                        if r.status_code == 200:
                            print(json.dumps(r.json(), indent = 4, sort_keys = True))
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.app_id:
                        url += "?app_id=%s" % args.app_id
                        r = requests.delete(url)
                        if r.status_code == 200:
                            print(json.dumps(r.json(), indent = 4, sort_keys = True))
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
                                print(json.dumps(r.json(), indent = 4, sort_keys = True))
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
                                r = requests.put(url, files = files, data = values)
                            else:
                                for key in values:
                                    values[key] = (None, values[key])
                                r = requests.put(url, files = values)
                            if r.status_code == 200:
                                print(json.dumps(r.json(), indent = 4, sort_keys = True))
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
                    r = requests.get(url)
                    if r.status_code == 200:
                        print(json.dumps(r.json(), indent = 4, sort_keys = True))
                    else:
                        print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                elif operation == "info":
                    if args.task_id:
                        url += "?task_id=%s" % args.task_id
                        r = requests.get(url)
                        if r.status_code == 200:
                            print(json.dumps(r.json(), indent = 4, sort_keys = True))
                        else:
                            print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
                    else:
                        parser.print_help()
                elif operation == "delete":
                    if args.task_id:
                        url += "?task_id=%s" % args.task_id
                        r = requests.delete(url)
                        if r.status_code == 200:
                            print(json.dumps(r.json(), indent = 4, sort_keys = True))
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
                                print(json.dumps(r.json(), indent = 4, sort_keys = True))
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
                                print(json.dumps(r.json(), indent = 4, sort_keys = True))
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
                        print(json.dumps(r.json(), indent = 4, sort_keys = True))
                    else:
                        print("error:\ncode: %s\ncontent: %s" % (r.status_code, r.content))
            else:
                parser.print_help()
        else:
            parser.print_help()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
