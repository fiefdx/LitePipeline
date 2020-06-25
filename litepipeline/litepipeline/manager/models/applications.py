# -*- coding: utf-8 -*-

import datetime
import logging
from uuid import uuid4

from litepipeline.manager.db.sqlite_interface import ApplicationsTable, NoResultFound, and_, or_, not_
from litepipeline.manager.config import CONFIG


LOG = logging.getLogger(__name__)


class Applications(object):
    _instance = None
    name = "applications"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.table = ApplicationsTable
            engine, session = ApplicationsTable.init_engine_and_session()
            cls._instance.table.metadata.create_all(engine)
            cls._instance.session = session(autoflush = False, autocommit = False)
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def _new_id(self):
        return str(uuid4())

    def add(self, name, sha1, description = ""):
        result = False
        app_id = self._new_id()
        now = datetime.datetime.now()
        item = {
            "application_id": app_id,
            "name": name,
            "create_at": now,
            "update_at": now,
            "sha1": sha1,
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
            result = row.to_dict()
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def parse_filters(self, filters):
        result = []
        try:
            if "id" in filters:
                result.append(self.table.application_id == filters["id"])
            if "name" in filters:
                result.append(self.table.name.like("%s" % filters["name"].replace("*", "%%")))
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset = 0, limit = 0, filters = {}):
        result = {"apps": [], "total": 0}
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
                result["apps"].append(row.to_dict())
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
