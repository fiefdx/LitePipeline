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

from litepipeline.manager.utils import common
from litepipeline.manager.config import CONFIG

LOG = logging.getLogger(__name__)


BaseApplications = declarative_base()

class ApplicationsTable(BaseApplications):
    __tablename__ = "applications"

    id = Column(Integer, primary_key = True, autoincrement = True)
    application_id = Column(Text, unique = True, nullable = False, index = True)
    name = Column(Text, nullable = False)
    create_at = Column(DateTime, nullable = False, index = True)
    update_at = Column(DateTime, nullable = False, index = True)
    sha1 = Column(Text, nullable = False)
    description = Column(Text)

    @classmethod
    def init_engine_and_session(cls):
        cls.engine = create_engine('sqlite:///' + os.path.join(CONFIG["data_path"], "applications.db"), echo = False)
        cls.session = sessionmaker(bind = cls.engine)
        return cls.engine, cls.session

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


BaseTasks = declarative_base()

class TasksTable(BaseTasks):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key = True, autoincrement = True)
    task_id = Column(Text, unique = True, nullable = False, index = True)
    task_name = Column(Text, nullable = False)
    application_id = Column(Text, nullable = False, index = True)
    create_at = Column(DateTime, nullable = False, index = True)
    start_at = Column(DateTime)
    update_at = Column(DateTime, nullable = False, index = True)
    end_at = Column(DateTime)
    stage = Column(Text, nullable = False, index = True)
    status = Column(Text)
    input_data = Column(Text)
    result = Column(Text)

    @classmethod
    def init_engine_and_session(cls):
        cls.engine = create_engine('sqlite:///' + os.path.join(CONFIG["data_path"], "tasks.db"), echo = False)
        cls.session = sessionmaker(bind = cls.engine)
        return cls.engine, cls.session

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "application_id": self.application_id,
            "create_at": str(self.create_at),
            "start_at": str(self.start_at) if self.start_at else self.start_at,
            "update_at": str(self.update_at),
            "end_at": str(self.end_at) if self.end_at else self.end_at,
            "stage": self.stage,
            "status": self.status,
            "input_data": json.loads(self.input_data),
            "result": json.loads(self.result),
        }

    def parse_dict(self, source):
        result = False

        attrs = [
            "task_id",
            "task_name",
            "application_id",
            "create_at",
            "start_at",
            "update_at",
            "end_at",
            "stage",
            "status",
            "input_data",
            "result",
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


BaseSchedules = declarative_base()

class SchedulesTable(BaseSchedules):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key = True, autoincrement = True)
    schedule_id = Column(Text, unique = True, nullable = False, index = True)
    schedule_name = Column(Text, nullable = False)
    application_id = Column(Text, nullable = False, index = True)
    create_at = Column(DateTime, nullable = False, index = True)
    update_at = Column(DateTime, nullable = False, index = True)
    input_data = Column(Text)
    minute = Column(Integer, nullable = True) # [0, 59]
    hour = Column(Integer, nullable = True) # [0, 23]
    day_of_month = Column(Integer, nullable = True) # [1, 31]
    day_of_week = Column(Integer, nullable = True) # [1, 7] (Sunday = 7)
    enable = Column(Boolean, nullable = False)

    @classmethod
    def init_engine_and_session(cls):
        cls.engine = create_engine('sqlite:///' + os.path.join(CONFIG["data_path"], "schedules.db"), echo = False)
        cls.session = sessionmaker(bind = cls.engine)
        return cls.engine, cls.session

    def to_dict(self):
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "schedule_name": self.schedule_name,
            "application_id": self.application_id,
            "create_at": str(self.create_at),
            "update_at": str(self.update_at),
            "input_data": json.loads(self.input_data),
            "minute": self.minute,
            "hour": self.hour,
            "day_of_month": self.day_of_month,
            "day_of_week": self.day_of_week,
            "enable": self.enable,
        }

    def parse_dict(self, source):
        result = False

        attrs = [
            "schedule_id",
            "schedule_name",
            "application_id",
            "create_at",
            "update_at",
            "input_data",
            "minute",
            "hour",
            "day_of_month",
            "day_of_week",
            "enable",
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
        return "schedule: %s" % self.to_dict()
