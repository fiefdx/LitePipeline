#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import stat
import argparse
from pathlib import Path

from litepipeline.version import __version__

cwd = os.path.split(os.path.realpath(__file__))[0]
parser = argparse.ArgumentParser(prog = 'liteconfig')

# common arguments
parser.add_argument("-s", "--service", required = True, help = "configuration service (manager, node)")
parser.add_argument("-o", "--output", required = True, help = "configuration file output path")
parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)

args = parser.parse_args()


def main():
    try:
        service = args.service
        output = args.output
        manager_path = os.path.join(cwd, "../manager")
        node_path = os.path.join(cwd, "../node")
        viewer_path = os.path.join(cwd, "../viewer")
        if service in ("manager", "node", "viewer"):
            if os.path.exists(output) and os.path.isdir(output):
                output = str(Path(output).resolve())
                log_path = os.path.join(output, "logs")
                data_path = os.path.join(output, "data")
                content = ""
                if service == "manager":
                    manager_config_file = os.path.join(manager_path, "configuration.yml.temp")
                    fp = open(manager_config_file, "r")
                    content = fp.read()
                    fp.close()
                    copy_files = [
                        "install_systemd_service.sh",
                        "uninstall_systemd_service.sh",
                        "litepipeline-manager.service.temp",
                        "manager.sh",
                        "README.md",
                        "migrate_database.py",
                    ]
                    for file_name in copy_files:
                        file_path_source = os.path.join(manager_path, file_name)
                        with open(file_path_source, "r") as fs:
                            file_path_target = os.path.join(output, file_name)
                            with open(file_path_target, "w") as ft:
                                ft.write(fs.read())
                            if file_path_target.endswith(".sh"):
                                os.chmod(
                                    file_path_target,
                                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IEXEC | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
                                )
                elif service == "node":
                    node_config_file = os.path.join(node_path, "configuration.yml.temp")
                    fp = open(node_config_file, "r")
                    content = fp.read()
                    fp.close()
                    copy_files = [
                        "install_systemd_service.sh",
                        "uninstall_systemd_service.sh",
                        "litepipeline-node.service.temp",
                        "node.sh",
                        "README.md",
                    ]
                    for file_name in copy_files:
                        file_path_source = os.path.join(node_path, file_name)
                        with open(file_path_source, "r") as fs:
                            file_path_target = os.path.join(output, file_name)
                            with open(file_path_target, "w") as ft:
                                ft.write(fs.read())
                            if file_path_target.endswith(".sh"):
                                os.chmod(
                                    file_path_target,
                                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IEXEC | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
                                )
                elif service == "viewer":
                    viewer_config_file = os.path.join(viewer_path, "configuration.yml.temp")
                    fp = open(viewer_config_file, "r")
                    content = fp.read()
                    fp.close()
                    copy_files = [
                        "install_systemd_service.sh",
                        "uninstall_systemd_service.sh",
                        "litepipeline-viewer.service.temp",
                        "viewer.sh",
                        "README.md",
                    ]
                    for file_name in copy_files:
                        file_path_source = os.path.join(viewer_path, file_name)
                        with open(file_path_source, "r") as fs:
                            file_path_target = os.path.join(output, file_name)
                            with open(file_path_target, "w") as ft:
                                ft.write(fs.read())
                            if file_path_target.endswith(".sh"):
                                os.chmod(
                                    file_path_target,
                                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IEXEC | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
                                )
                content = content.replace("log_path_string", log_path)
                content = content.replace("data_path_string", data_path)
                fp = open(os.path.join(output, "configuration.yml"), "w")
                fp.write(content)
                fp.close()
            else:
                print("output(%s) not exists!", output)
        else:
            print("service must by manager or node, not %s", service)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
