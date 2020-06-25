# -*- coding: utf-8 -*-

import os
import logging
import argparse

from sqlalchemy import Index

from litepipeline.version import __version__
from litepipeline.manager.db.sqlite_interface import ApplicationsTable
from litepipeline.manager.db.sqlite_interface import TasksTable
from litepipeline.manager.db.sqlite_interface import WorkflowsTable
from litepipeline.manager.db.sqlite_interface import WorksTable
from litepipeline.manager.db.sqlite_interface import SchedulesTable
from litepipeline.manager.config import CONFIG, load_config
from litepipeline.manager import logger

LOG = logging.getLogger(__name__)


application_name_index = Index('ix_applications_name', ApplicationsTable.name)

task_name_index = Index('ix_tasks_task_name', TasksTable.task_name)
task_start_at_index = Index('ix_tasks_start_at', TasksTable.start_at)
task_end_at_index = Index('ix_tasks_end_at', TasksTable.end_at)
task_status_index = Index('ix_tasks_status', TasksTable.status)

workflow_name_index = Index('ix_workflows_name', WorkflowsTable.name)

work_name_index = Index('ix_works_name', WorksTable.name)
work_start_at_index = Index('ix_works_start_at', WorksTable.start_at)
work_end_at_index = Index('ix_works_end_at', WorksTable.end_at)
work_status_index = Index('ix_works_status', WorksTable.status)

schedule_name_index = Index('ix_schedules_name', SchedulesTable.schedule_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = 'migrate_database.py')
    parser.add_argument("-c", "--config", required = True, help = "configuration file path")
    parser.add_argument("-v", "--version", action = 'version', version = '%(prog)s ' + __version__)
    args = parser.parse_args()
    if args.config:
        success = load_config(args.config)
        if success:
            logger.config_logging(file_name = "migrate_database.log",
                                  log_level = CONFIG["log_level"],
                                  dir_name = CONFIG["log_path"],
                                  day_rotate = False,
                                  when = "D",
                                  interval = 1,
                                  max_size = 20,
                                  backup_count = 5,
                                  console = True)

            LOG.info("migrate start")
            engine, _ = ApplicationsTable.init_engine_and_session()
            application_name_index.create(bind = engine)

            engine, _ = TasksTable.init_engine_and_session()
            task_name_index.create(bind = engine)
            task_start_at_index.create(bind = engine)
            task_end_at_index.create(bind = engine)
            task_status_index.create(bind = engine)

            engine, _ = WorkflowsTable.init_engine_and_session()
            workflow_name_index.create(bind = engine)

            engine, _ = WorksTable.init_engine_and_session()
            work_name_index.create(bind = engine)
            work_start_at_index.create(bind = engine)
            work_end_at_index.create(bind = engine)
            work_status_index.create(bind = engine)

            engine, _ = SchedulesTable.init_engine_and_session()
            schedule_name_index.create(bind = engine)

            LOG.info("migrate end")
        else:
            print("failed to load configuration: %s" % args.config)
    else:
        parser.print_help()