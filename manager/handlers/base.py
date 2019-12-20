# -*- coding: utf-8 -*-

import logging

import tornado.web
import tornado.locale
import tornado.websocket

LOG = logging.getLogger(__name__)

class BaseHandler(tornado.web.RequestHandler):
    # def get_current_user(self):
    #     return self.get_secure_cookie("user", max_age_days = 1)

    # def get_current_user_key(self):
    #     return self.get_secure_cookie("user_key", max_age_days = 1)

    # def get_user_locale_value(self):
    #     user_locale = self.get_secure_cookie("user_locale", max_age_days = 1)
    #     if user_locale:
    #         return user_locale
    #     return None

    def set_default_headers(self):
        self.set_header("Content-Type", 'application/json')

    def get_user_locale(self):
        pass
        # user_locale = self.get_secure_cookie("user_locale", max_age_days = 1)
        # if user_locale:
        #     return tornado.locale.get(user_locale)
        # return None
    # def __init__(self, application, request, **kwargs):
    #     super(BaseHandler, self).__init__(application, request, kwargs)
    #     self.locale_code = "en_US"
    # pass

class BaseSocketHandler(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        pass
        # return self.get_secure_cookie("user", max_age_days = 1)

    # def get_current_user_key(self):
    #     return self.get_secure_cookie("user_key", max_age_days = 1)

    # def get_user_locale(self):
    #     user_locale = self.get_secure_cookie("user_locale", max_age_days = 1)
    #     if user_locale:
    #         return tornado.locale.get(user_locale)
    #     return None