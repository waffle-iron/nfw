# Neutrino Framework
#
# Copyright (c) 2016-2017, Christiaan Frans Rademan
# All rights reserved.
#
# LICENSE: (BSD3-Clause)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENTSHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import os
import logging
import pickle
import time
import datetime
import fcntl
if sys.version[0] == '2':
    import thread
    from Cookie import SimpleCookie
else:
    import _thread as thread
    from http.cookies import SimpleCookie
import threading

import nfw

log = logging.getLogger(__name__)

lock = threading.Lock()


class SessionBase(object):
    def __init__(self, config, **kwargs):
        self._thread_id = thread.get_ident() 
        self.headers = nfw.Headers()
        app_config = config.get('application')
        self.use_x_forwarded_host = app_config.get('use_x_forwarded_host', False)
        self._name = None
        self._expire = app_config.get('session_expire', 3600)
        self._id = None
        if 'app_root' in kwargs:
            self._path = "%s/tmp/" % (kwargs['app_root'],)
        if 'redis' in kwargs:
            self._redis = kwargs['redis']

    def _get_host(self, environ):
        if self.use_x_forwarded_host is True and 'X_FORWARDED_HOST' in self.headers:
            return self.headers['X_FORWARDED_HOST']
        elif 'HOST' in self.headers:
            return self.headers['HOST']
        elif 'SERVER_NAME' in self.environ:
            return self.environ['SERVER_NAME']
        elif 'SERVER_ADDR' in self.environ:
            return self.environ['SERVER_ADDR']
        else:                                                                       
            return None

    def setup(self, environ):
        for p in environ:                                                           
            if len(p) > 5 and 'HTTP_' in p:
                hk = p.replace('HTTP_', '')
                self.headers[hk] = environ[p]

        self.environ = environ

        cookie = SimpleCookie()
        name = nfw.utils.if_unicode_to_utf8('neutrino')

        if 'HTTP_COOKIE' in self.environ:
            cookie.load(self.environ['HTTP_COOKIE'])
        if name in cookie:
            id = nfw.utils.if_unicode_to_utf8(cookie[name].value)
        else:
            id = nfw.utils.if_unicode_to_utf8(nfw.random_id(16))

        self._id = nfw.utils.if_unicode_to_utf8(id)
        self._name = "session:%s" % (id,)
        cookie[name] = nfw.utils.if_unicode_to_utf8(id)
        host = self._get_host(environ)
        if host is not None:
            cookie[name]['domain'] = host
        cookie[name]['max-age'] = self._expire

        cookie_string = cookie[name].OutputString()
        if hasattr(self, '_load'):
            self._load()
        return cookie_string

    def save(self):
        if hasattr(self, '_save'):
            self._save()


class SessionRedis(SessionBase):
    def _save(self):
        self._redis.expire(self._name, self._expire)

    def __setitem__(self, key, value):
        self._redis.hset(self._name, key, value)
        self._redis.expire(self._name, self._expire)

    def __getitem__(self, key):
        val = self._redis.hget(self._name, key)
        if val == 'True':
            return True
        elif val == 'False':
            return False
        else:
            return val

    def __delitem__(self, key):
        self._redis.hdel(self._name, key)

    def __contains__(self, key):
        return self._redis.hexists(self._name, key)

    def __iter__(self):
        return iter(self._redis.hgetall(self._name))

    def __len__(self):
        return hlen(self._redis.hlen(self._name))

    def get(self, k, d=None):
        if k in self:
            val = self._redis.hget(self._name, k)
            if val == 'True':
                return True
            elif val == 'False':
                return False
            else:
                return val
        else:
            return d


class SessionFile(SessionBase):
    def _load(self):
        lock.acquire()
        try:
            if os.path.isfile("%s%s.session" % (self._path, self._id,)):
                ts = int(time.mktime(datetime.datetime.now().timetuple()))
                stat = os.stat("%s%s.session" % (self._path, self._id))
                lm = int(stat.st_mtime)
                if ts - lm > self._expire:
                    self._session = {}

            if os.path.isfile("%s%s.session" % (self._path, self._id,)):
                h = open("%s%s.session" % (self._path, self._id,), 'rb', 0)
                fcntl.flock(h, fcntl.LOCK_EX)
                try:
                    self._session = pickle.load(h)
                finally:
                    fcntl.flock(h, fcntl.LOCK_UN)
                    h.close()
            else:
                self._session = {}
        finally:
            lock.release()

    def _save(self):
        lock.acquire()
        try:
            h = open("%s%s.session" % (self._path, self._id,), 'wb', 0)
            fcntl.flock(h, fcntl.LOCK_EX)
            pickle.dump(self._session, h)
            h.flush()
            fcntl.flock(h, fcntl.LOCK_UN)
        finally:
            h.close()
            lock.release()

    def __setitem__(self, key, value):
        self._session[key] = value

    def __getitem__(self, key):
        return self._session[key]

    def __delitem__(self, key):
        try:
            del self._session[key]
        except KeyError:
            pass

    def __contains__(self, key):
        return key in self._session

    def __iter__(self):
        return iter(self._session)

    def __len__(self):
        return len(self._session)

    def get(self, k, d=None):
        return self._session.get(k, d)
