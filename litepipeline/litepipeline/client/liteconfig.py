#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import argparse

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
        manager_config_file = os.path.join(cwd, "../manager/configuration.yml")
        node_config_file = os.path.join(cwd, "../node/configuration.yml")
        if service in ("manager", "node"):
            if os.path.exists(output) and os.path.isdir(output):
                content = ""
                if service == "manager":
                    fp = open(manager_config_file, "r")
                    content = fp.read()
                    fp.close()
                elif service == "node":
                    fp = open(node_config_file, "r")
                    content = fp.read()
                    fp.close()
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
