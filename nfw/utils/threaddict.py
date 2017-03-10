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
import logging
if sys.version[0] == '2':
    import thread
else:
    import _thread as thread
import threading

threads = {}

lock = threading.Lock()

log = logging.getLogger(__name__)


class ThreadDict(object):
    def __init__(self):
        global threads
        lock.acquire()
        try:
            self._thread_id = thread.get_ident()
            if self._thread_id not in threads:
                threads[self._thread_id] = {}
            self.data = threads[self._thread_id]
        finally:
            lock.release()

    def __setitem__(self, key, value):
        lock.acquire()
        try:
            self.data[key] = value
        finally:
            lock.release()

    def __getitem__(self, key):
        if key in self.data:
            return self.get(key)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        lock.acquire()
        try:
            del self.data[key]
        finally:
            lock.release()

    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)

    def update(self, update):
        lock.acquire()
        try:
            self.data.update(update)
        finally:
            lock.release()

    def get(self, key, default=None):
        return self.data.get(key, default)
