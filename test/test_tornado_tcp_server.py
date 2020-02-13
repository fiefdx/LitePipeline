# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

from tornado.ioloop import IOLoop
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.options import options, define

from litepipeline.manager import logger

LOG = logging.getLogger(__name__)

cwd = os.path.split(os.path.realpath(__file__))[0]

define("port", default=6001, help="TCP port to listen on")


class EchoServer(TCPServer):
    @gen.coroutine
    def handle_stream(self, stream, address):
        while True:
            try:
                data = yield stream.read_until(b"\n")
                LOG.info("Received bytes: %s", data)
                if not data.endswith(b"\n"):
                    data = data + b"\n"
                yield stream.write(data)
            except StreamClosedError:
                LOG.warning("Lost client at host %s", address[0])
                break
            except Exception as e:
                print(e)



if __name__ == "__main__":
    logger.config_logging(file_name = "test_tornado_tcp.log",
                          log_level = "DEBUG",
                          dir_name = os.path.join(cwd, "logs"),
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)

    LOG.debug("test start")
    
    try:
        options.parse_command_line()
        server = EchoServer()
        server.listen(options.port)
        LOG.info("Listening on TCP port %d", options.port)
        IOLoop.current().start()
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
