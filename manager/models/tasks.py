# -*- coding: utf-8 -*-

import json
import datetime
import logging
from uuid import uuid4

from db.sqlite_interface import SessionTasks, EngineTasks, TasksTable, NoResultFound
from utils.common import Status, Stage
from config import CONFIG

LOG = logging.getLogger(__name__)


class Tasks(object):
    def __init__(self, *kargs, **kwargs):
        self.table = TasksTable
        self.table.metadata.create_all(EngineTasks)
        self.session = SessionTasks(autoflush = False, autocommit = False)

    def _new_id(self):
        return str(uuid4())

    def add(self, task_name, app_id, stage = Stage.pending, source = {}):
        result = False
        task_id = self._new_id()
        now = datetime.datetime.now()
        item = {
            "task_id": task_id,
            "task_name": task_name,
            "application_id": app_id,
            "create_at": now,
            "update_at": now,
            "stage": stage,
            "source": json.dumps(source),
            "result": json.dumps({}),
        }

        row = self.table()
        row.parse_dict(item)
        try:
            self.session.add(row)
            self.session.commit()
            result = task_id
            LOG.debug("add task: %s", row)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def update(self, task_id, data):
        result = False
        try:
            now = datetime.datetime.now()
            if "source" in data:
                data["source"] = json.dumps(data["source"])
            if "result" in data:
                data["result"] = json.dumps(data["result"])
            data["update_at"] = now
            self.session.query(self.table).filter_by(task_id = task_id).update(data)
            self.session.commit()
            result = True
            LOG.debug("update task: %s, %s", task_id, data)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete(self, task_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(task_id = task_id).one()
            self.session.delete(row)
            self.session.commit()
            result = True
            LOG.debug("delete task: %s", row)
        except Exception as e:
            LOG.exception(e)
        return result

    def get(self, task_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(task_id = task_id).one()
            result = row.to_dict()
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def get_first(self, stage = Stage.pending):
        result = False
        try:
            row = self.session.query(self.table).filter_by(stage = stage).order_by(self.table.start_at.asc()).first()
            if row:
                result = row.to_dict()
            else:
                result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset = 0, limit = 0, stage = ""):
        result = []
        try:
            offset = 0 if offset < 0 else offset
            limit = 0 if limit < 0 else limit
            if stage and hasattr(Stage, stage):
                if limit:
                    rows = self.session.query(self.table).filter_by(stage = stage).order_by(self.table.start_at.desc()).offset(offset).limit(limit)
                elif offset:
                    rows = self.session.query(self.table).filter_by(stage = stage).order_by(self.table.start_at.desc()).offset(offset)
                else:
                    rows = self.session.query(self.table).filter_by(stage = stage).order_by(self.table.start_at.desc())
            else:
                if limit:
                    rows = self.session.query(self.table).order_by(self.table.start_at.desc()).offset(offset).limit(limit)
                elif offset:
                    rows = self.session.query(self.table).order_by(self.table.start_at.desc()).offset(offset)
                else:
                    rows = self.session.query(self.table).order_by(self.table.start_at.desc())
            for row in rows:
                result.append(row.to_dict())
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        self.session.close()


TasksDB = Tasks()
