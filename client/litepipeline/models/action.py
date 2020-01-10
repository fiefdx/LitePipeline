# -*- coding: utf-8 -*-

import os
import sys
import json
import logging

LOG = logging.getLogger(__name__)


class InvalidInputError(Exception):
    def __init__(self, message):
        self.message = message


class Action(object):
    def __init__(self, name, main, condition = [], env = None, input_data = {}, to_action = None):
        self.name = name
        self.main = main
        self.condition = condition
        self.env = env
        self.input_data = input_data
        self.to_action = to_action

    def to_dict(self):
        result = {
            "name": self.name,
            "main": self.main,
            "condition": self.condition,
            "input_data": self.input_data,
        }
        if self.to_action:
            result["to_action"] = self.to_action
        if self.env:
            result["env"] = self.env
        return result

    @classmethod
    def get_input(cls):
        print("argv: %s" % sys.argv)
        if len(sys.argv) < 2:
            raise InvalidInputError("invalid argv: %s" % sys.argv)
        else:
            cls.workspace = sys.argv[1]
            if os.path.exists(cls.workspace) and os.path.isdir(cls.workspace):
                fp = open(os.path.join(cls.workspace, "input.data"), "r")
                cls.input_data = json.loads(fp.read())
                fp.close()
                return cls.workspace, cls.input_data
            else:
                raise InvalidInputError("workspace[%s] not exists" % workspace)

    @classmethod
    def set_output(cls, data = {}, actions = []):
        result = {"data": {}, "actions": []}
        if data:
            result["data"] = data
        for action in actions:
            result["actions"].append(action.to_dict())
        fp = open(os.path.join(cls.workspace, "output.data"), "w")
        fp.write(json.dumps(result, indent = 4))
        fp.close()
