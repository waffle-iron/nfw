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

import os
import signal
import sys
import logging
import inspect
import io
import cgi
if sys.version[0] == '2':
    import thread
else:
    import _thread as thread
import json
import traceback
import keyword
import re

from jinja2 import Environment as jinja2
from jinja2.exceptions import TemplateNotFound

import nfw

log = logging.getLogger(__name__)


class Wsgi(object):
    def __init__(self, app_root):
        nfw.app = self
        self.app_root = app_root.rstrip('/')
        config = "%s/settings.cfg" % (self.app_root,)
        policy = "%s/policy.json" % (self.app_root,)
        self.config = nfw.Config(config)
        self.app_config = self.config.get('application')
        self.log_config = self.config.get('logging')
        app_name = self.app_config.get('name','neutrino')
        host = self.log_config.get('host')
        port = self.log_config.get('port', 514)
        debug = self.log_config.getboolean('debug')
        self.logger = nfw.Logger(app_name, host, port, debug)
        log.info("STARTING APPLICATION PROCESS FOR %s" % (app_name,))
        if debug is True:
            nfw.restart.start(interval=1.0)
            nfw.restart.track(config)
            nfw.restart.track(policy)

        self.router = nfw.Router()
        self.views = []
        self.context = {}
        nfw.jinja = nfw.template.Jinja(self.config)
        modules = self.app_config.getitems('modules')
        self.modules = self._modules()
        nfw.jinja.load_templates()
        nfw.render_template = nfw.template.Jinja.render_template
        middleware = self.app_config.getitems('middleware')
        self.middleware = self._m_objs(self.modules, middleware)
        if os.path.isfile(policy):
            policy = file(policy, 'r').read()
            self.policy = json.loads(policy)
        else:
            self.policy = None

    def _error_template(self, req, code):
        for module in self.modules:
            try:
                t = nfw.jinja.get_template("%s.html" % (code))
                return t
            except TemplateNotFound:
                pass
            try:
                if req.is_ajax():
                    t = nfw.jinja.get_template("%s/%s_ajax.html" % (module, code))
                    return t
                else:
                    t = nfw.jinja.get_template("%s/%s.html" % (module, code))
                    return t

            except TemplateNotFound:
                pass

        return None

    def _error(self, e, req, resp):
        if hasattr(e, 'headers'):
            resp.headers.update(e.headers)

        if hasattr(e, 'status'):
            resp.status = e.status
        else:
            resp.status = nfw.HTTP_500

        if hasattr(e, 'code'):
            code = e.code
        else:
            code = resp.status.split(" ")[0]

        if hasattr(e, 'title'):
            title = e.title
        else:
            title = None

        if hasattr(e, 'description'):
            description = e.description
        else:
            description = repr(e)

        resp.clear()
        if resp.headers.get('Content-Type') == nfw.TEXT_PLAIN:
            if title is not None:
                resp.write("%s\n" % (title,))
            if description is not None:
                resp.write("%s" % (description,))
        elif resp.headers.get('Content-Type') == nfw.TEXT_HTML:
            t = self._error_template(req, code)
            if t is not None:
                resp.body = t.render(title=title, description=description)
            else:
                dom = nfw.web.Dom()
                html = dom.create_element('html')
                head = html.create_element('head')
                t = head.create_element('title')
                t.append(resp.status)
                body = html.create_element('body')
                if title is not None:
                    h1 = body.create_element('h1')
                    h1.append(title)
                if description is not None:
                    h2 = body.create_element('h2')
                    h2.append(description)
                resp.body = dom.get()
        elif resp.headers.get('Content-Type') == nfw.APPLICATION_JSON:
            j = {'error': {'title': title, 'description': description}}
            resp.body = json.dumps(j)
        else:
            if title is not None:
                resp.write("%s\n" % (title,))
            if description is not None:
                resp.write("%s" % (description,))

        return resp

    def _cleanup(self):
        nfw.RestClient().close_all()
        nfw.Mysql.close_all()
        self.logger.stdout.flush()
        sys.stdout.flush()
        sys.stderr.flush()

    # The application interface is a callable object
    def _interface(self, environ, start_response):
        # environ points to a dictionary containing CGI like environment
        # variables which is populated by the server for each
        # received request from the client
        # start_response is a callback function supplied by the server
        # which takes the HTTP status and headers as arguments

        # When the method is POST the variable will be sent
        # in the HTTP request body which is passed by the WSGI server
        # in the file like wsgi.input environment variable.
        debug = self.log_config.getboolean('debug')

        if 'redis' in self.config:
            redis = nfw.redis(self.config)
            session = nfw.SessionRedis(self.config, redis=redis)
        else:
            session = nfw.SessionFile(self.config, app_root=self.app_root)
        session_cookie = session.setup(environ)

        mysql_config = self.config.get('mysql')
        if mysql_config.get('database') is not None:
            nfw.Mysql(**mysql_config.data)

        req = nfw.Request(environ, self.config, session, self.router, self.logger, self)
        resp = nfw.Response(req)

        resp.headers['Set-Cookie'] = session_cookie

        r = self.router.route(req)

        if debug is True:
            log.debug("Request URI: %s" % (req.get_full_path()))
            log.debug("Request QUERY: %s" % (req.environ['QUERY_STRING'],))

        response_headers = []

        nfw.jinja.globals['SITE'] = req.environ['SCRIPT_NAME']
        nfw.jinja.request['REQUEST'] = req
        if nfw.jinja.globals['SITE'] == '/':
            nfw.jinja.globals['SITE'] = ''
        nfw.jinja.globals['STATIC'] = self.app_config.get('static',
                                                          '').rstrip('/')
        if nfw.jinja.globals['STATIC'] == '/':
            nfw.jinja.globals['STATIC'] = ''


        returned = None
        try:
            if r is not None:
                route, obj_kwargs = r
                method, route, obj, name = route
                req.args = obj_kwargs
                req.view = name
            else:
                obj_kwargs = {}

            policy = nfw.Policy(self.policy,
                                context=req.context,
                                session=req.session,
                                kwargs=obj_kwargs,
                                qwargs=req.query)
            req.policy = policy

            for m in self.middleware:
                if hasattr(m, 'pre'):
                    m.pre(req, resp)

            if r is not None:
                if policy.validate(req.view):
                    returned = nfw.utils.if_unicode_to_utf8(obj(req, resp, **obj_kwargs))
                else:
                    raise nfw.HTTPForbidden('Access Forbidden',
                                            'Access denied by application policy')
            else:
                raise nfw.HTTPNotFound(description=req.environ['PATH_INFO'])

            for m in reversed(self.middleware):
                if hasattr(m, 'post'):
                    m.post(req, resp)

        except nfw.HTTPError as e:
            if debug is True:
                trace = str(traceback.format_exc())
                log.error("%s\n%s" % (e, trace))
            self._error(e, req, resp)
        except Exception as e:
            trace = str(traceback.format_exc())
            log.error("%s\n%s" % (e, trace))
            self._error(e, req, resp)

        resp.headers['X-Powered-By'] = 'Neutrino'
        resp.headers['X-Request-ID'] = req.request_id
        # HTTP headers expected by the client
        # They must be wrapped as a list of tupled pairs:
        # [(Header name, Header value)].
        for header in resp.headers:
            header = nfw.utils.if_unicode_to_utf8(header)
            value = nfw.utils.if_unicode_to_utf8(resp.headers[header])
            h = (header, value)
            response_headers.append(h)

        content_length = None

        if returned is None:
            content_length = resp.content_length
        else:
            if isinstance(returned, str):
                content_length = len(returned)

        if content_length is not None:
            response_headers.append(('Content-Length'.encode('utf-8'),
                                     str(content_length).encode('utf-8')))

        # Send status and headers to the server using the supplied function
        start_response(resp.status, response_headers)

        self._cleanup()
        session.save()

        if returned is not None:
            return returned
        else:
            return resp

    def _modules(self):
        app_config = self.config.get('application')
        loaded = {}
        modules = app_config.getitems('modules')
        for module in modules:
            m = nfw.utils.import_module(module)
            loaded[module] = m

        return loaded

    def _m_objs(self, modules, middleware):
        loaded = []
        for m in middleware:
            z = m.split('.')
            if len(z) > 1:
                l = len(z)
                mod = z[0:l-1]
                mod = '.'.join(mod)
                cls = z[l-1]
                if mod in modules:
                    mod = modules[mod]
                    if hasattr(mod, cls):
                        cls = getattr(mod, cls)
                        try:
                            loaded.append(cls(self))
                        except Exception as e:
                            trace = str(traceback.format_exc())
                            log.error("%s\n%s" % (str(e), trace))
                    else:
                        raise ImportError(m)
                else:
                    raise ImportError(m)
            else:
                raise ImportError(m)
        return loaded

    def resources(self):
        def resource_wrapper(f):
            return self.views.append(f(self))

        return resource_wrapper

    def resource(self, method, resource, policy=None):
        def resource_wrapper(f):
            return self.router.add(method, resource, f, policy)

        return resource_wrapper

    def application(self):
        # Return the application interface method as a callable object
        return self._interface
