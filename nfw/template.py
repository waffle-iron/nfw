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
import sys
import logging
import traceback
if sys.version[0] == '2':
    import thread
else:
    import _thread as thread

from pkg_resources import DefaultProvider, ResourceManager, \
                          get_provider
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from jinja2.utils import open_if_exists, internalcode
from jinja2._compat import string_types, iteritems
from jinja2.loaders import BaseLoader
from jinja2 import loaders
import threading

import nfw

log = logging.getLogger(__name__)

lock = threading.Lock()


class GetTemplateWrapper(object):
    def __init__(self, template, request):
        self._request = request
        self._template = template
   
    def render(self, **kwargs):
        for r in self._request:
            kwargs[r] = self._request[r]
        return self._template.render(**kwargs)


class Jinja(object):
    def __init__(self, config):
        self.config = config
        self.app_config = self.config.get('application')
        self.modules = self.app_config.getitems('modules')
        self._request = nfw.ThreadDict()
        self._loader = nfw.template.JinjaLoader(self.modules)
        self._jinja = Environment(loader=self._loader)

    def get_template(self, *args, **kwargs):
        t = self._jinja.get_template(*args, **kwargs)
        w = GetTemplateWrapper(t, self._request)
        return w

    def render_template(self, template, **kwargs):
        t = self.get_template(template)
        return t.render(**kwargs)

    def __getattr__(self, attr):
        lock.acquire()
        try:
            if attr == 'request':
                return self._request
            elif attr == 'load_templates':
                return self._loader.load_templates 
            elif attr == 'globals':
                return getattr(self._jinja, attr)
            elif attr == 'list_templates':
                return getattr(self._jinja, attr)
            else:
                raise Exception("Neutrino Jinja Environment has no attribute %s" % (attr,))
        finally:
            lock.release()


class JinjaLoader(BaseLoader):
    def __init__(self, packages):
        self.searchpath = ['templates']
        try:
            self.fsl = loaders.FileSystemLoader(self.searchpath)
        except Exception as e:
            log.error(e)

        self.modules = packages
        self.packages = {}
        self.encoding = 'utf-8'
        self.package_path = "templates"
        self.manager = ResourceManager()

    def load_templates(self):
        for package_name in self.modules:
            try:
                pkg = self.packages[package_name] = {}
                pkg['provider'] = get_provider(package_name)
                pkg['fs_bound'] = isinstance(pkg['provider'], DefaultProvider)
            except Exception as e:
                trace = str(traceback.format_exc())
                log.error("Can't import module %s\n%s" % (str(e), trace))

    def get_source(self, environment, template):
        pieces = loaders.split_template_path(template)
        try:
            return self.fsl.get_source(environment, template)
        except Exception as e:
            pass

        if len(pieces) > 1 and pieces[0] in self.packages:
            pkg_name = pieces[0]
            pkg = self.packages[pkg_name]
            del pieces[0]
            p = '/'.join((self.package_path,) + tuple(pieces))
            if not pkg['provider'].has_resource(p):
                raise TemplateNotFound(template)
        else:
            raise TemplateNotFound(template)

        filename = uptodate = None
        if pkg['fs_bound']:
            filename = pkg['provider'].get_resource_filename(self.manager, p)
            mtime = os.path.getmtime(filename)

            def uptodate():
                try:
                    return os.path.getmtime(filename) == mtime
                except OSError:
                    return False

        source = pkg['provider'].get_resource_string(self.manager, p)
        return source.decode(self.encoding), filename, uptodate

    def list_templates(self):
        fsl = []
        try:
            #fsl = self.fsl.get_source(environment, template)
            pass
        except Exception as e:
            log.error(e)

        path = self.package_path
        if path[:2] == './':
            path = path[2:]
        elif path == '.':
            path = ''
        offset = len(path)
        results = []

        def _walk(path,pkg):
            for filename in pkg['provider'].resource_listdir(path):
                fullname = path + '/' + filename
                if pkg['provider'].resource_isdir(fullname):
                    _walk(fullname, pkg)
                else:
                    p = fullname[offset:].lstrip('/')
                    p = "%s/%s" % (package_name, p)
                    results.append(p)
        for package_name in self.packages:
            pkg = self.packages[package_name]
            if pkg['provider'].resource_isdir(path):
                _walk(path,pkg)
        results.sort()

        return results + fsl
