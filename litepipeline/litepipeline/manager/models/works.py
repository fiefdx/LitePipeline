# -*- coding: utf-8 -*-

import json
import datetime
import logging
from uuid import uuid4

from litepipeline.manager.db.sqlite_interface import WorksTable, NoResultFound
from litepipeline.manager.utils.common import Status, Stage
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger(__name__)


class Works(object):
    _instance = None
    name = "works"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.table = WorksTable
            engine, session = WorksTable.init_engine_and_session()
            cls._instance.table.metadata.create_all(engine)
            cls._instance.session = session(autoflush = False, autocommit = False)
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def _new_id(self):
        return str(uuid4())

    def add(self, name, workflow_id, stage = Stage.pending, input_data = {}, configuration = {}):
        result = False
        work_id = self._new_id()
        now = datetime.datetime.now()
        item = {
            "work_id": work_id,
            "name": name,
            "workflow_id": workflow_id,
            "create_at": now,
            "update_at": now,
            "stage": stage,
            "input_data": json.dumps(input_data),
            "configuration": json.dumps(configuration),
            "result": json.dumps({}),
        }

        row = self.table()
        row.parse_dict(item)
        try:
            self.session.add(row)
            self.session.commit()
            result = work_id
            LOG.debug("add work: %s", row)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def update(self, work_id, data):
        result = False
        try:
            now = datetime.datetime.now()
            if "input_data" in data:
                data["input_data"] = json.dumps(data["input_data"])
            if "configuration" in data:
                data["configuration"] = json.dumps(data["configuration"])
            if "result" in data:
                data["result"] = json.dumps(data["result"])
            data["update_at"] = now
            self.session.query(self.table).filter_by(work_id = work_id).update(data)
            self.session.commit()
            result = True
            LOG.debug("update work: %s, %s", work_id, data)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete(self, work_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(work_id = work_id).one()
            self.session.delete(row)
            self.session.commit()
            result = True
            LOG.debug("delete work: %s", row)
        except Exception as e:
            LOG.exception(e)
        return result

    def get(self, work_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(work_id = work_id).one()
            result = row.to_dict()
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def get_first(self, stages = [Stage.pending, Stage.recovering]):
        result = False
        try:
            row = self.session.query(self.table).filter(self.table.stage.in_(stages)).order_by(self.table.create_at.asc()).first()
            if row:
                result = row.to_dict()
            else:
                result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def parse_filters(self, filters):
        result = []
        try:
            if "work_id" in filters:
                result.append(self.table.work_id == filters["work_id"])
            if "workflow_id" in filters:
                result.append(self.table.workflow_id == filters["workflow_id"])
            if "name" in filters:
                result.append(self.table.name.like("%s" % filters["name"].replace("*", "%%")))
            if "stage" in filters:
                result.append(self.table.stage == filters["stage"])
            if "status" in filters:
                result.append(self.table.status == filters["status"])
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset = 0, limit = 0, filters = {}):
        result = {"works": [], "total": 0}
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
                result["works"].append(row.to_dict())
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
