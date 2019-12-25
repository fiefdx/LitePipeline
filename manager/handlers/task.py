# -*- coding: utf-8 -*-

import json
import time
import logging

from tornado import web
from tornado import gen

from handlers.base import BaseHandler, BaseSocketHandler
from config import CONFIG

LOG = logging.getLogger("__name__")


class CreateTaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class RunTaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class StopTaskHandler(BaseHandler): # kill -9 or -15
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class DeleteTaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class InfoTaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class ListTaskHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()


class CleanTaskHistoryHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {}
        self.write(result)
        self.finish()
