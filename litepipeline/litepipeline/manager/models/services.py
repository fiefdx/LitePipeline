# -*- coding: utf-8 -*-

import json
import datetime
import logging
from uuid import uuid4

from litepipeline.manager.db.sqlite_interface import ServicesTable, NoResultFound
from litepipeline.manager.utils.common import Status, Stage
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger(__name__)


class Services(object):
    _instance = None
    name = "services"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.table = ServicesTable
            engine, session = ServicesTable.init_engine_and_session()
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
        services = self.list()["services"]
        for service in services:
            service_id = service["service_id"]
            self.cache[service_id] = service

    def add(self, name, app_id, description = "", enable = False, input_data = {}, signal = -9):
        result = False
        service_id = self._new_id()
        now = datetime.datetime.now()
        if signal not in (-9, -15):
            signal = -9
        item = {
            "service_id": service_id,
            "name": name,
            "application_id": app_id,
            "task_id": "",
            "create_at": now,
            "update_at": now,
            "stage": "",
            "status": "",
            "input_data": json.dumps(input_data),
            "description": description,
            "signal": signal,
            "enable": enable,
        }

        row = self.table()
        row.parse_dict(item)
        try:
            self.session.add(row)
            self.session.commit()
            self.cache[service_id] = row.to_dict()
            result = service_id
            LOG.debug("add service: %s", row)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def update(self, service_id, data):
        result = False
        try:
            now = datetime.datetime.now()
            if "input_data" in data:
                data["input_data"] = json.dumps(data["input_data"])
            data["update_at"] = now
            if "signal" in data and data["signal"] not in (-9, -15):
                data["signal"] = -9
            self.session.query(self.table).filter_by(service_id = service_id).update(data)
            self.session.commit()
            if "input_data" in data:
                data["input_data"] = json.loads(data["input_data"])
            data["update_at"] = str(now)
            if service_id in self.cache:
                self.cache[service_id].update(data)
            else:
                service = self.get(service_id)
                self.cache[service_id] = service
            result = True
            LOG.debug("update service: %s, %s", service_id, data)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete(self, service_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(service_id = service_id).one()
            self.session.delete(row)
            self.session.commit()
            if service_id in self.cache:
                del self.cache[service_id]
            result = True
            LOG.debug("delete service: %s", row)
        except Exception as e:
            LOG.exception(e)
        return result

    def get(self, service_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(service_id = service_id).one()
            result = row.to_dict()
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def parse_filters(self, filters):
        result = []
        try:
            if "service_id" in filters:
                result.append(self.table.service_id == filters["service_id"])
            if "app_id" in filters:
                result.append(self.table.application_id == filters["app_id"])
            if "task_id" in filters:
                result.append(self.table.task_id == filters["task_id"])
            if "name" in filters:
                result.append(self.table.name.like("%s" % filters["name"].replace("*", "%%")))
            if "enable" in filters:
                result.append(self.table.enable == filters["enable"])
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset = 0, limit = 0, filters = {}):
        result = {"services": [], "total": 0}
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
                result["services"].append(row.to_dict())
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
