# -*- coding: utf-8 -*-

import json
import datetime
import logging
from uuid import uuid4

from litepipeline.manager.db.sqlite_interface import SchedulesTable, NoResultFound
from litepipeline.manager.utils.common import Status, Stage
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger(__name__)


class Schedules(object):
    _instance = None
    name = "schedules"
    application = "application"
    workflow = "workflow"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.table = SchedulesTable
            engine, session = SchedulesTable.init_engine_and_session()
            cls._instance.table.metadata.create_all(engine)
            cls._instance.session = session(autoflush = False, autocommit = False)
            cls._instance.cache = {}
            cls._instance.load_cache()
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def _new_id(self):
        return str(uuid4())

    def load_cache(self):
        schedules = self.list(filters = {"enable": True})["schedules"]
        for schedule in schedules:
            schedule_id = schedule["schedule_id"]
            self.cache[schedule_id] = schedule

    def add(self, schedule_name, source, source_id, minute = -1, hour = -1, day_of_month = -1, day_of_week = -1, enable = False, input_data = {}):
        result = False
        schedule_id = self._new_id()
        now = datetime.datetime.now()
        item = {
            "schedule_id": schedule_id,
            "schedule_name": schedule_name,
            "source": source,
            "source_id": source_id,
            "create_at": now,
            "update_at": now,
            "minute": minute,
            "hour": hour,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "input_data": json.dumps(input_data),
            "enable": enable,
        }

        row = self.table()
        row.parse_dict(item)
        try:
            self.session.add(row)
            self.session.commit()
            self.cache[schedule_id] = row.to_dict()
            result = schedule_id
            LOG.debug("add schedule: %s", row)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def update(self, schedule_id, data):
        result = False
        try:
            now = datetime.datetime.now()
            if "input_data" in data:
                data["input_data"] = json.dumps(data["input_data"])
            data["update_at"] = now
            self.session.query(self.table).filter_by(schedule_id = schedule_id).update(data)
            self.session.commit()
            if "input_data" in data:
                data["input_data"] = json.loads(data["input_data"])
            data["update_at"] = str(now)
            if schedule_id in self.cache:
                if "enable" in data and not data["enable"]:
                    del self.cache[schedule_id]
                else:
                    self.cache[schedule_id].update(data)
            else:
                schedule = self.get(schedule_id)
                if schedule["enable"]:
                    self.cache[schedule_id] = schedule
            result = True
            LOG.debug("update schedule: %s, %s", schedule_id, data)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete(self, schedule_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(schedule_id = schedule_id).one()
            self.session.delete(row)
            self.session.commit()
            if schedule_id in self.cache:
                del self.cache[schedule_id]
            result = True
            LOG.debug("delete schedule: %s", row)
        except Exception as e:
            LOG.exception(e)
        return result

    def get(self, schedule_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(schedule_id = schedule_id).one()
            result = row.to_dict()
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def parse_filters(self, filters):
        result = []
        try:
            if "schedule_id" in filters:
                result.append(self.table.schedule_id == filters["schedule_id"])
            if "source_id" in filters:
                result.append(self.table.source_id == filters["source_id"])
            if "name" in filters:
                result.append(self.table.schedule_name.like("%s" % filters["name"].replace("*", "%%")))
            if "enable" in filters:
                result.append(self.table.enable == filters["enable"])
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset = 0, limit = 0, filters = {}):
        result = {"schedules": [], "total": 0}
        try:
            offset = 0 if offset < 0 else offset
            limit = 0 if limit < 0 else limit
            filters = self.parse_filters(filters)
            result["total"] = self.count(filters)
            if filters:
                if limit:
                    rows = self.session.query(self.table).filter(*filters).order_by(self.table.create_at.desc()).offset(offset).limit(limit)
                elif offset:
                    rows = self.session.query(self.table).filter(*filters).order_by(self.table.create_at.desc()).offset(offset)
                else:
                    rows = self.session.query(self.table).filter(*filters).order_by(self.table.create_at.desc())
            else:
                if limit:
                    rows = self.session.query(self.table).order_by(self.table.create_at.desc()).offset(offset).limit(limit)
                elif offset:
                    rows = self.session.query(self.table).order_by(self.table.create_at.desc()).offset(offset)
                else:
                    rows = self.session.query(self.table).order_by(self.table.create_at.desc())
            for row in rows:
                result["schedules"].append(row.to_dict())
        except Exception as e:
            LOG.exception(e)
        return result

    def count(self, filters):
        result = 0
        try:
            if filters:
                result = self.session.query(self.table).filter(*filters).count()
            else:
                result = self.session.query(self.table).count()
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        self.session.close()
