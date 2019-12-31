# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.ioloop import IOLoop
from tornado import gen

cwd = os.path.split(os.path.realpath(__file__))[0]
sys.path.insert(0, os.path.split(cwd)[0])

import logger

LOG = logging.getLogger(__name__)

fp = open("./test.tar.gz", "wb")

def on_done(response):
    print(response)
    fp.close()

@gen.coroutine
def on_chunk(chunk):
    print(len(chunk))
    fp.write(chunk)
    

if __name__ == "__main__":
    logger.config_logging(file_name = "test_tornado_httpclient_async.log",
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
        url = "http://127.0.0.1:8000/app/download?app_id=d6c1341c-a40b-44e3-91dd-de4042ef5346"
        client = AsyncHTTPClient()
        request = HTTPRequest(url = url, streaming_callback = on_chunk)
        client.fetch(request, on_done)
        IOLoop.current().start()
    except Exception as e:
        LOG.exception(e)

    LOG.debug("test end")
