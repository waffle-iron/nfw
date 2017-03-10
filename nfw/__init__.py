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

_cc = 0


class EmptyApp(object):
    def resources(self):
        def resource_wrapper(f):
            return f

        return resource_wrapper 

    def resource(self, *args, **kwargs):
        def resource_wrapper(f):
            return f

        return resource_wrapper


app = EmptyApp()


import os
import signal

def creation_counter():
    global _cc
    _cc += 1
    return _cc

from . import restart
from .version import __version__ as version
from .exceptions import *

from .constants import *
from . import utils
from .utils import random_id, timer, ThreadDict

from . import config
from .config import Config

from .logger import Logger
from . import mysql
from .mysql import Mysql
from .redissy import redis
from .session import SessionRedis
from .session import SessionFile
from .policy import Policy
from .router import Router
from .router import view
from .request import Request
from .response import Response
from .response import http_moved_permanently
from .response import http_found
from .response import http_see_other
from .response import http_temporary_redirect
from .response import http_permanent_redirect
from .headers import Headers
from . import password
from . import template
from .wsgi import Wsgi
from . import model
from .model import Model
from .model import ModelDict
from . import web
from . import restclient
from .restclient import RestClient
from .web import bootstrap3
from . import restapi


