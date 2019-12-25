# -*- coding: utf-8 -*-

import os
import json
import logging

import sqlalchemy
from sqlalchemy import func, exc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, Date, DateTime, Numeric
from sqlalchemy.orm.exc import NoResultFound

from config import CONFIG

LOG = logging.getLogger(__name__)

BaseApplications = declarative_base()
EngineApplications = create_engine('sqlite:///' + os.path.join(CONFIG["data_path"], "applications.db"), echo = False)
SessionApplications = sessionmaker(bind = EngineApplications)

class ApplicationsTable(BaseApplications):
    __tablename__ = "applications"

    id = Column(Integer, primary_key = True, autoincrement = True)
    application_id = Column(Text, unique = True, nullable = False, index = True)
    name = Column(Text, nullable = False)
    create_at = Column(DateTime, nullable = False, index = True)
    update_at = Column(DateTime, nullable = False, index = True)
    sha1 = Column(Text, nullable = False)
    description = Column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "name": self.name,
            "create_at": str(self.create_at), # "%Y-%m-%d %H:%M:%S.%f")
            "update_at": str(self.update_at),
            "sha1": self.sha1,
            "description": self.description,
        }

    def parse_dict(self, source):
        result = False

        attrs = [
            "application_id",
            "name", 
            "create_at", 
            "update_at",
            "sha1",
            "description",
        ]

        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
        return result

    def __repr__(self):
        return "application: %s" % self.to_dict()


BaseTasksStatus = declarative_base()
EngineTasksStatus = create_engine('sqlite:///' + os.path.join(CONFIG["data_path"], "tasks_status.db"), echo = False)
SessionTasksStatus = sessionmaker(bind = EngineTasksStatus)

class TasksStatusTable(BaseTasksStatus):
    __tablename__ = "tasks_status"

    id = Column(Integer, primary_key = True, autoincrement = True)
    task_id = Column(Text, unique = True, nullable = False, index = True)
    task_name = Column(Text, nullable = False)
    application_id = Column(Text, unique = True, nullable = False, index = True)
    application_name = Column(Text, nullable = False)
    start_at = Column(DateTime, nullable = False, index = True)
    update_at = Column(DateTime, nullable = False, index = True)
    end_at = Column(DateTime)
    status = Column(Text, nullable = False)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "application_id": self.application_id,
            "application_name": self.application_name,
            "start_at": str(self.start_at),
            "update_at": str(self.update_at),
            "end_at": str(self.end_at),
            "status": self.status,
        }

    def parse_dict(self, source):
        result = False

        attrs = [
            "task_id",
            "task_name",
            "application_id",
            "application_name",
            "start_at",
            "update_at",
            "end_at",
            "status",
        ]

        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
        return result

    def __repr__(self):
        return "task: %s" % self.to_dict()


BaseTasks = declarative_base()
EngineTasks = create_engine('sqlite:///' + os.path.join(CONFIG["data_path"], "tasks.db"), echo = False)
SessionTasks = sessionmaker(bind = EngineTasks)

class TasksTable(BaseTasks):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key = True, autoincrement = True)
    task_id = Column(Text, unique = True, nullable = False, index = True)
    task_name = Column(Text, nullable = False)
    application_id = Column(Text, nullable = False, index = True)
    start_at = Column(DateTime, nullable = False, index = True)
    source = Column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "application_id": self.application_id,
            "start_at": str(self.start_at),
            "source": json.loads(self.source),
        }

    def parse_dict(self, source):
        result = False

        attrs = [
            "task_id",
            "task_name",
            "application_id",
            "start_at",
            "source",
        ]

        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
        return result

    def __repr__(self):
        return "task: %s" % self.to_dict()
