# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

from tornado.ioloop import IOLoop
from tornado import gen
from tornado.tcpclient import TCPClient
from tornado.options import options, define

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

import logger

LOG = logging.getLogger(__name__)

define("host", default="localhost", help="TCP server host")
define("port", default=6001, help="TCP port to connect to")
define("message", default="ping", help="Message to send")


@gen.coroutine
def send_message():
    stream = yield TCPClient().connect(options.host, options.port)
    yield stream.write((options.message + "\n").encode())
    print("Sent to server:", options.message)
    reply = yield stream.read_until(b"\n")
    print("Response from server:", reply.decode().strip())
    

if __name__ == "__main__":
    logger.config_logging(file_name = "test_tornado_tcp_client.log",
                          log_level = "DEBUG",
                          dir_name = "logs",
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)

    LOG.debug("test start")
    
    try:
        options.parse_command_line()
        IOLoop.current().run_sync(send_message)
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
