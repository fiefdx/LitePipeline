# -*- coding: utf-8 -*-

import datetime
import logging
from uuid import uuid4

from litepipeline.manager.db.sqlite_interface import ApplicationHistoryTable, NoResultFound, and_, or_, not_
from litepipeline.manager.config import CONFIG


LOG = logging.getLogger(__name__)


class ApplicationHistory(object):
    _instance = None
    name = "application_history"

    def __new__(cls):
        if not cls._instance:
            cls._instance = object.__new__(cls)
            cls._instance.table = ApplicationHistoryTable
            engine, session = ApplicationHistoryTable.init_engine_and_session()
            cls._instance.table.metadata.create_all(engine)
            cls._instance.session = session(autoflush = False, autocommit = False)
        return cls._instance

    @classmethod
    def instance(cls):
        return cls._instance

    def add(self, app_id, sha1, description = ""):
        result = False
        now = datetime.datetime.now()
        item = {
            "application_id": app_id,
            "create_at": now,
            "sha1": sha1,
            "description": description,
        }

        row = self.table()
        row.parse_dict(item)
        try:
            self.session.add(row)
            self.session.commit()
            result = row.id
            LOG.debug("add application history: %s", row)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete(self, history_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(id = history_id).one()
            self.session.delete(row)
            self.session.commit()
            result = row.to_dict()
            LOG.debug("delete application history: %s", row)
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete_by_app_id(self, app_id):
        result = False
        try:
            self.session.query(self.table).filter_by(application_id = app_id).delete()
            self.session.commit()
            result = True
            LOG.debug("delete application[%s] all history", app_id)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def delete_by_history_id_app_id(self, history_id, app_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(id = history_id).filter_by(application_id = app_id).one()
            self.session.delete(row)
            self.session.commit()
            result = row.to_dict()
            LOG.debug("delete application[%s] history[%s]", app_id, history_id)
        except Exception as e:
            LOG.exception(e)
            self.session.rollback()
        return result

    def get(self, history_id, app_id = ""):
        result = False
        try:
            if app_id:
                row = self.session.query(self.table).filter_by(id = history_id).filter_by(application_id = app_id).one()
            else:
                row = self.session.query(self.table).filter_by(id = history_id).one()
            result = row.to_dict()
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def get_latest(self, app_id):
        result = False
        try:
            row = self.session.query(self.table).filter_by(application_id = app_id).order_by(self.table.create_at.desc()).first()
            result = row.to_dict()
        except NoResultFound:
            result = None
        except Exception as e:
            LOG.exception(e)
        return result

    def parse_filters(self, filters):
        result = []
        try:
            if "app_id" in filters:
                result.append(self.table.application_id == filters["app_id"])
            if "sha1" in filters:
                result.append(self.table.sha1 == filters["sha1"])
        except Exception as e:
            LOG.exception(e)
        return result

    def list(self, offset = 0, limit = 0, filters = {}):
        result = {"histories": [], "total": 0}
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
                result["histories"].append(row.to_dict())
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
