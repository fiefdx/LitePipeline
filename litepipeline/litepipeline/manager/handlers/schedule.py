# -*- coding: utf-8 -*-

import json
import time
import urllib
import logging

from tornado import web
from tornado import gen

from litepipeline.manager.handlers.base import BaseHandler, BaseSocketHandler
from litepipeline.manager.models.applications import Applications
from litepipeline.manager.models.schedules import Schedules
from litepipeline.manager.utils.common import file_sha1sum, file_md5sum, Errors, Stage, splitall, JSONLoadError
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger("__name__")


class CreateScheduleHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        result = {"result": Errors.OK}
        try:
            self.json_data = json.loads(self.request.body.decode("utf-8"))
            schedule_name = self.get_json_argument("schedule_name", "")
            app_id = self.get_json_argument("app_id", "")
            input_data = self.get_json_argument("input_data", {})
            minute = int(self.get_json_argument("minute", -1))             # [0, 59]
            hour = int(self.get_json_argument("hour", -1))                 # [0, 23]
            day_of_month = int(self.get_json_argument("day_of_month", -1)) # [1, 31]
            month = int(self.get_json_argument("month", -1))               # [1, 12]
            day_of_week = int(self.get_json_argument("day_of_week", -1))   # [0, 6] (Sunday = 0)
            enable = True if self.get_json_argument("enable", False) else False
            if (
                    app_id and
                    Applications.instance().get(app_id) and
                    schedule_name and
                    (minute == -1 or (minute >= 0 and minute <= 59)) and
                    (hour == -1 or (hour >= 0 and hour <= 23)) and
                    (day_of_month == -1 or (day_of_month >= 1 and day_of_month <= 31)) and
                    (month == -1 or (month >= 1 and month <= 12)) and
                    (day_of_week == -1 or (day_of_week >= 0 and day_of_week <= 6))
                ):
                if not isinstance(input_data, dict):
                    raise JSONLoadError("input_data must be dict type")
                schedule_id = Schedules.instance().add(
                    schedule_name,
                    app_id,
                    minute = minute,
                    hour = hour,
                    day_of_month = day_of_month,
                    month = month,
                    day_of_week = day_of_week,
                    enable = enable,
                    input_data = input_data
                )
                if schedule_id is not False:
                    result["schedule_id"] = schedule_id
                else:
                    Errors.set_result_error("OperationFailed", result)
            else:
                LOG.warning("invalid arguments")
                Errors.set_result_error("InvalidParameters", result)
            LOG.debug("CreateTaskHandler, schedule_name: %s, app_id: %s", schedule_name, app_id)
        except JSONLoadError as e:
            LOG.error(e)
            Errors.set_result_error("InvalidParameters", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class DeleteScheduleHandler(BaseHandler):
    @gen.coroutine
    def delete(self):
        result = {"result": Errors.OK}
        try:
            schedule_id = self.get_argument("schedule_id", "")
            if schedule_id:
                success = Schedules.instance().delete(schedule_id)
                if not success:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class InfoScheduleHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            schedule_id = self.get_argument("schedule_id", "")
            if schedule_id:
                schedule_info = Schedules.instance().get(schedule_id)
                if schedule_info:
                    result["schedule_info"] = schedule_info
                    if schedule_id in Schedules.instance().cache:
                        result["schedule_cache_info"] = Schedules.instance().cache[schedule_id]
                elif schedule_info is None:
                    Errors.set_result_error("ScheduleNotExists", result)
                else:
                    Errors.set_result_error("OperationFailed", result)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()


class ListScheduleHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        result = {"result": Errors.OK}
        try:
            offset = int(self.get_argument("offset", "0"))
            limit = int(self.get_argument("limit", "0"))
            enable = self.get_argument("enable", None)
            if enable == "true":
                enable = True
            elif enable == "false":
                enable = False
            else:
                enable = None
            LOG.debug("ListScheduleHandler offset: %s, limit: %s, enable: %s", offset, limit, enable)
            result["schedules"] = Schedules.instance().list(offset = offset, limit = limit, enable = enable)
        except Exception as e:
            LOG.exception(e)
            Errors.set_result_error("ServerException", result)
        self.write(result)
        self.finish()
