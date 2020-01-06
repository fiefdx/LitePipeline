#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import json
import argparse

import requests

parser = argparse.ArgumentParser()
parser.add_argument("address", help = "manager address, host:port")
parser.add_argument("object", help = "object: [app, task, cluster]")
parser.add_argument("operation", help = "app's operations: [create, delete, update, list, info, download], task's operations: [create, delete, list, info]")
parser.add_argument("-a", "--app_id", help = "application id", default = "")
parser.add_argument("-t", "--task_id", help = "task id", default = "")
parser.add_argument("-d", "--description", help = "application's description", default = "")
parser.add_argument("-n", "--name", help = "application's/task's name", default = "")
parser.add_argument("-f", "--file", help = "application's file", default = "")
parser.add_argument("-o", "--offset", help = "list offset", type = int, default = 0)
parser.add_argument("-l", "--limit", help = "list limit", type = int, default = 0)
parser.add_argument("-i", "--input", help = "task's input data, json string", default = "{}")
parser.add_argument("-s", "--stage", help = "task's executing stage: [pending, running, finished]", default = "")
parser.add_argument("-g", "--signal", help = "stop task's signal: -9 or -15", type = int, default = -15)
parser.add_argument("-v", "--verbosity", help = "increase output verbosity", action = "store_true")
args = parser.parse_args()
app_operations = ["create", "delete", "update", "list", "info", "download"]
task_operations = ["create", "delete", "list", "info", "stop"]
cluster_operations = ["info"]


def main():
    try:
        print("*" * 10 + " litepipeline command line tool " + "*" * 10)
        address = args.address
        object = args.object
        operation = args.operation
        url = "http://%s/%s/%s" % (address, object, operation)
        if address:
            if object == "app":
                if operation in app_operations:
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
                else:
                    parser.print_help()
            elif object == "task":
                if operation in task_operations:
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
                else:
                    parser.print_help()
            elif object == "cluster":
                if operation in cluster_operations:
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
