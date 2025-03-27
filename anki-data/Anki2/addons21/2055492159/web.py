# Copyright 2016-2021 Alex Yatskov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import json
import jsonschema
import http.server
import socketserver
from threading import Thread
from . import util

#
# WebRequest
#

class WebRequest:
    def __init__(self, method, headers, body):
        self.method = method
        self.headers = headers
        self.body = body


#
# WebClient
#

class WebClient:
    def __init__(self, sock, handler):
        self.sock = sock
        self.handler = handler
        self.readBuff = bytes()
        self.writeBuff = bytes()


    def advance(self, recvSize=1024):
        if self.sock is None:
            return False

        rlist, wlist = select.select([self.sock], [self.sock], [], 0)[:2]
        self.sock.settimeout(5.0)

        if rlist:
            while True:
                try:
                    msg = self.sock.recv(recvSize)
                except (ConnectionResetError, socket.timeout):
                    self.close()
                    return False
                if not msg:
                    self.close()
                    return False
                self.readBuff += msg

                req, length = self.parseRequest(self.readBuff)
                if req is not None:
                    self.readBuff = self.readBuff[length:]
                    self.writeBuff += self.handler(req)
                    break



        if wlist and self.writeBuff:
            try:
                length = self.sock.send(self.writeBuff)
                self.writeBuff = self.writeBuff[length:]
                if not self.writeBuff:
                    self.close()
                    return False
            except:
                self.close()
                return False
        return True


    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

        self.readBuff = bytes()
        self.writeBuff = bytes()


    def parseRequest(self, data):
        parts = data.split('\r\n\r\n'.encode('utf-8'), 1)
        if len(parts) == 1:
            return None, 0

        lines = parts[0].split('\r\n'.encode('utf-8'))
        method = None

        if len(lines) > 0:
            request_line_parts = lines[0].split(' '.encode('utf-8'))
            method = request_line_parts[0].upper() if len(request_line_parts) > 0 else None

        headers = {}
        for line in lines[1:]:
            pair = line.split(': '.encode('utf-8'))
            headers[pair[0].lower()] = pair[1] if len(pair) > 1 else None

        headerLength = len(parts[0]) + 4
        bodyLength = int(headers.get('content-length'.encode('utf-8'), 0))
        totalLength = headerLength + bodyLength

        if totalLength > len(data):
            return None, 0

        body = data[headerLength : totalLength]
        return WebRequest(method, headers, body), totalLength

#
# WebServer
#

class WebServer:
    def __init__(self, handler):
        self.handler = handler
        self.server = None
        self.thread = None

    def start(self):
        class RequestHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self2):
                content_length = int(self2.headers['Content-Length'])
                body = self2.rfile.read(content_length).decode('utf-8')
                try:
                    params = json.loads(body)
                    result = self.handler(params)
                    response = json.dumps(result).encode('utf-8')
                    self2.send_response(200)
                    self2.send_header('Content-Type', 'application/json')
                    self2.send_header('Access-Control-Allow-Origin', '*')
                    self2.send_header('Content-Length', len(response))
                    self2.end_headers()
                    self2.wfile.write(response)
                except Exception as e:
                    error_response = json.dumps(format_exception_reply(6, str(e))).encode('utf-8')
                    self2.send_response(500)
                    self2.send_header('Content-Type', 'application/json')
                    self2.send_header('Access-Control-Allow-Origin', '*')
                    self2.send_header('Content-Length', len(error_response))
                    self2.end_headers()
                    self2.wfile.write(error_response)

            def do_OPTIONS(self2):
                self2.send_response(200)
                self2.send_header('Access-Control-Allow-Origin', '*')
                self2.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self2.send_header('Access-Control-Allow-Headers', '*')
                self2.end_headers()

        self.server = socketserver.TCPServer(('0.0.0.0', 8765), RequestHandler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

def format_success_reply(api_version, result):
    return {
        "result": result,
        "error": None
    }

def format_exception_reply(_api_version, exception):
    return {
        "result": None,
        "error": str(exception)
    }


request_schema = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "minLength": 1},
        "version": {"type": "integer"},
        "params": {"type": "object"},
    },
    "required": ["action"],
}
