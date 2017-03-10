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

import io
import sys
import logging

if sys.version[0] == '2':
    from StringIO import StringIO
else:
    from io import StringIO

import nfw

log = logging.getLogger(__name__)


def http_moved_permanently(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = nfw.HTTP_301
    resp.headers['Location'] = url


def http_found(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = nfw.HTTP_302
    resp.headers['Location'] = url


def http_see_other(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = nfw.HTTP_303
    resp.headers['Location'] = url


def http_temporary_redirect(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = nfw.HTTP_307
    resp.headers['Location'] = url


def http_permanent_redirect(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = nfw.HTTP_308
    resp.headers['Location'] = url


class Response(object):
    _attributes = ['status']

    def __init__(self, req=None):
        self.status = nfw.HTTP_200
        super(Response, self).__setattr__('headers', nfw.Headers(request=False))
        self.headers['Content-Type'] = nfw.TEXT_HTML
        super(Response, self).__setattr__('_io', StringIO())
        super(Response, self).__setattr__('content_length', 0)
        super(Response, self).__setattr__('_req', req)
        self.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        self.headers['Progma'] = 'no-cache'
        self.headers['Expires'] = 0

    def __setattr__(self, name, value):
        if name in self._attributes:
            super(Response, self).__setattr__(name, value)
        elif name == 'body':
            self.clear()
            super(Response, self).__setattr__('_io', StringIO())
            self.write(value)
        else:
            AttributeError("'response' object can't bind" +
                           " attribute '%s'" % (name,))

    def seek(self,position):
        self._io.seek(position)

    def read(self, size=0):
        if size == 0:
            return self._io.read()
        else:
            return self._io.read(size)

    def readline(self, size=0):
        if size == 0:
            return self._io.readline()
        else:
            return self._io.readline(size)

    def write(self, data):
        data = nfw.utils.if_unicode_to_utf8(data)
        super(Response, self).__setattr__('content_length',
                                          len(data)+self.content_length)
        self._io.write(data)

    def clear(self):
        super(Response, self).__setattr__('content_length', 0)
        super(Response, self).__setattr__('_io', StringIO())

    def __iter__(self):
        self._io.seek(0)
        return ResponseIoStream(self._io)

    def view(self, url, method):
        self.clear()
        nfw.view(url, method, self._req, self)

    def redirect(self, url):
        self.clear()
        http_see_other(url, self._req, self)


def ResponseIoStream(f, chunk_size=None):
    '''Genereator to buffer chunks'''
    while True:
        if chunk_size is None:
            chunk = f.read()
        else:
            chunk = f.read(chunk_size)
        if not chunk:
            break
        yield nfw.utils.if_unicode_to_utf8(chunk)
