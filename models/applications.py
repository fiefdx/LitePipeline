# -*- coding: utf-8 -*-

import datetime
import logging
from uuid import uuid4

from db.sqlite_interface import SessionApplications, EngineApplications, ApplicationsTable
from config import CONFIG

LOG = logging.getLogger(__name__)


class Applications(object):
    def __init__(self, *kargs, **kwargs):
        self.table = ApplicationsTable
        self.table.metadata.create_all(EngineApplications)
        self.session = SessionApplications(autoflush = False, autocommit = False)

    def _new_id(self):
        return str(uuid4())

    def add(self, name, description = ""):
        result = False
        app_id = self._new_id()
        now = datetime.datetime.now()
        item = {
            "application_id": app_id,
            "name": name,
            "create_at": now,
            "update_at": now,
            "description": description,
        }

        row = self.table()
        row.parse_dict(item)
        try:
            self.session.add(row)
            self.session.commit()
            result = app_id
            LOG.debug("add application: %s", row)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def update(self, app_id, data):
        result = False
        try:
            now = datetime.datetime.now()
            data["update_at"] = now
            self.session.query(self.table).filter_by(application_id = app_id).update(data)
            self.session.commit()
            result = True
            LOG.debug("update application: %s, %s", app_id, data)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete(self, app_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(application_id = app_id).one()
            self.session.delete(row)
            self.session.commit()
            result = True
            LOG.debug("delete application: %s", row)
        except Exception as e:
            LOG.exception(e)
        return result

    def get(self, app_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(application_id = app_id).one()
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


ApplicationsDB = Applications()
