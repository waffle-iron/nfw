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
from __future__ import unicode_literals

import sys
import logging
import re
if sys.version[0] == '2':
    import thread
else:
    import _thread as thread

try:
    # python 3
    from io import BytesIO
except ImportError:
    # python 2
    from StringIO import StringIO as BytesIO
try:
    # python 3
    from urllib.parse import urlencode
except ImportError:
    # python 2
    from urllib import urlencode

import nfw

log = logging.getLogger(__name__)

curl_sessions = {}


def _debug(debug_type, debug_msg):
    log.debug("(%d): %s" % (debug_type, debug_msg))

class RestClient(object):
    def __init__(self, ssl_verify=False, ssl_verify_peer=True,
                 ssl_verify_host=True, ssl_cacert=None,
                 ssl_cainfo=None, timeout=30, connect_timeout=2):

        global curl_sessions

        if ssl_verify is True:
            if ssl_verify_peer is True:
                self.ssl_verify_peer = 1
            else:
                self.ssl_verify_peer = 0

            if ssl_verify_host is True:
                self.ssl_verify_host = 2
            else:
                self.ssl_verify_host = 0
        else:
                self.ssl_verify_peer = 0
                self.ssl_verify_host = 0

        self.ssl_cacert = ssl_cacert
        self.ssl_cainfo = ssl_cainfo
        self.timeout = timeout
        self.connect_timeout = connect_timeout

        self.thread_id = thread.get_ident()
        if self.thread_id not in curl_sessions:
            curl_sessions[self.thread_id] = {}
        self.curl_session = curl_sessions[self.thread_id]

    def header_function(self, header_line):
        # HTTP standard specifies that headers are encoded in iso-8859-1.
        # On Python 2, decoding step can be skipped.
        # On Python 3, decoding step is required.
        header_line = header_line.decode('iso-8859-1')

        # Header lines include the first status line (HTTP/1.x ...).
        # We are going to ignore all lines that don't have a colon in them.
        # This will botch headers that are split on multiple lines...
        if ':' not in header_line:
            return

        # Break the header line into header name and value.
        name, value = header_line.split(':', 1)

        # Remove whitespace that may be present.
        # Header lines include the trailing newline, and 
        # there may be whitespace around the colon.
        name = name.strip()
        value = value.strip()

        # Header names are case insensitive.
        # Lowercase name here.
        name = name.lower()

        # Now we can actually record the header name and value.
        self.server_headers[name] = value

    def get_host_port_from_url(self, url):
        url_splitted = url.split('/')
        host = "%s//%s" % (url_splitted[0], url_splitted[2])
        return host

    def execute(self, method, url, data=None, headers=[]):
        import pycurl
        host = self.get_host_port_from_url(url)
        if host in self.curl_session:
            curl = self.curl_session[host]
        else:
            self.curl_session[host] = pycurl.Curl()
            curl = self.curl_session[host]

        url = url.replace(" ", "%20")

        method = method.upper()

        self.server_headers = dict()

        buffer = BytesIO()

        curl.setopt(curl.URL, nfw.utils.if_unicode_to_utf8(url))
        try:
            curl.setopt(curl.WRITEDATA, buffer)
        except TypeError:
            curl.setopt(curl.WRITEFUNCTION, buffer.write)
        curl.setopt(curl.HEADERFUNCTION, self.header_function)
        curl.setopt(curl.FOLLOWLOCATION, True)
        curl.setopt(curl.SSL_VERIFYPEER, self.ssl_verify_peer)
        curl.setopt(curl.SSL_VERIFYHOST, self.ssl_verify_host)
        curl.setopt(curl.CONNECTTIMEOUT, self.connect_timeout)
        curl.setopt(curl.TIMEOUT, self.timeout)
        curl.setopt(curl.DEBUGFUNCTION, _debug)
        curl.setopt(curl.VERBOSE, 1)

        if data is not None:
            curl.setopt(curl.POSTFIELDS, nfw.utils.if_unicode_to_utf8(data))
        else:
            curl.setopt(curl.POSTFIELDS, nfw.utils.if_unicode_to_utf8(''))

        send_headers = list()
        for header in headers:
            send_header = nfw.utils.if_unicode_to_utf8("%s: %s" % (header,
                                                                   headers[header]))
            send_headers.append(send_header)

        curl.setopt(pycurl.HTTPHEADER, send_headers)

        if method == nfw.HTTP_GET:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('GET'))
        elif method == nfw.HTTP_PUT:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('PUT'))
        elif method == nfw.HTTP_POST:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('POST'))
        elif method == nfw.HTTP_PATCH:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('PATCH'))
        elif method == nfw.HTTP_DELETE:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('DELETE'))
        elif method == nfw.HTTP_OPTIONS:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('OPTIONS'))
        elif method == nfw.HTTP_HEAD:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('HEAD'))
        elif method == nfw.HTTP_TRACE:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('TRACE'))
        elif method == nfw.HTTP_CONNECT:
            curl.setopt(curl.CUSTOMREQUEST,
                        nfw.utils.if_unicode_to_utf8('CONNECT'))
        else:
            raise nfw.Error("Invalid request type %s" % (method,))

        try:
            curl.perform()
            status = curl.getinfo(pycurl.HTTP_CODE)
        except pycurl.error as e:
            del self.curl_session[host]
            if e[0] == 28:
                raise nfw.RestClientError("Connection timeout %s" % (host,))
            else:
                raise pycurl.error(e)

        # Figure out what encoding was sent with the response, if any.
        # Check against lowercased header name.
        encoding = None
        if 'content-type' in self.server_headers:
            content_type = self.server_headers['content-type'].lower()
            match = re.search('charset=(\S+)', content_type)
            if match:
                encoding = match.group(1)
        if encoding is None:
            # Default encoding for JSON is UTF-8.
            # Other content types may have different default encoding,
            # or in case of binary data, may have no encoding at all.
            encoding = 'utf_8'

        body = buffer.getvalue()
        # Decode using the encoding we figured out.
        body = body.decode(encoding)
        resp_header = nfw.Headers()
        for h in self.server_headers:
            resp_header[h] = self.server_headers[h]
        return (status, resp_header, body)

    def close_all(self):
        for session in self.curl_session:
            self.curl_session[session].close()
        self.thread_id = thread.get_ident()
        curl_sessions[self.thread_id] = {}
        self.curl_session = curl_sessions[self.thread_id]
