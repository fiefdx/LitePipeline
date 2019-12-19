# -*- coding: utf-8 -*-

import datetime
import logging
from uuid import uuid4

from db.sqlite_interface import SessionTasksStatus, EngineTasksStatus, TasksStatusTable
from config import CONFIG

LOG = logging.getLogger(__name__)


class TasksStatus(object):
    def __init__(self, *kargs, **kwargs):
        self.table = TasksStatusTable
        self.table.metadata.create_all(EngineTasksStatus)
        self.session = SessionTasksStatus(autoflush = False, autocommit = False)

    def add(self, task_id, task_name, app_id, app_name, start_at, status = ""):
        result = False
        now = datetime.datetime.now()
        item = {
            "task_id": task_id,
            "task_name": task_name,
            "application_id": app_id,
            "application_name": app_name,
            "start_at": start_at,
            "update_at": now,
            "status": status,
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
            result = row
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset = 0, limit = 0):
        result = []
        try:
            if limit:
                rows = self.session.query(self.table).order_by(self.table.update_at.desc()).offset(offset).limit(limit)
            else:
                rows = self.session.query(self.table).order_by(self.table.update_at.desc())
            for row in rows:
                result.append(row.to_dict())
        except Exception as e:
            LOG.exception(e)
        return result

    def close(self):
        self.session.close()


TasksStatusDB = TasksStatus()
