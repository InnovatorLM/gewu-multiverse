#!/usr/bin/env python3
"""Loopback DawnFM Responses gateway; upstream credential stays outside roles.

This is a transport component, not an approval or execution boundary. The broker
must provide role isolation and own this process's lifetime. No request bodies,
authorization headers or upstream error bodies are logged.
"""
import http.server
import hmac
import json
import requests

MODEL = 'deepseek-v4.1-flash-1017'
BASE = 'https://dawnfm.gravarc.cn/v1'
MAX_BODY = 8 * 1024 * 1024


def validate_request(path, body):
    if path != '/v1/responses':
        raise ValueError('Unsupported endpoint')
    if len(body) > MAX_BODY:
        raise ValueError('Request too large')
    data = json.loads(body)
    if not isinstance(data, dict) or data.get('model') != MODEL:
        raise ValueError('Designated model required')
    if data.get('background'):
        raise ValueError('Background execution refused')
    return data


def handler_type(key, forward=None, access_token=None):
    if not key or '\n' in key or '\r' in key:
        raise ValueError('Invalid upstream credential')
    session = requests.Session()
    if forward is None:
        forward = session.post

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'

        def log_message(self, *_):
            pass

        def do_POST(self):
            response = None
            try:
                if access_token is None or not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + access_token):
                    self.send_error(401, 'Gateway authorization required')
                    return
                if self.headers.get('Transfer-Encoding'):
                    raise ValueError('Chunked input refused')
                length = int(self.headers.get('Content-Length', '-1'))
                if not 0 <= length <= MAX_BODY:
                    raise ValueError('Invalid request length')
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError('Incomplete request')
                data = validate_request(self.path, body)
                response = forward(BASE + '/responses', json=data,
                                   headers={'Authorization': 'Bearer ' + key},
                                   stream=True, timeout=(15, 180), allow_redirects=False)
                if response.status_code != 200:
                    self.send_error(502, 'Upstream request failed')
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream' if data.get('stream') else 'application/json')
                self.end_headers()
                for block in response.iter_content(chunk_size=4096):
                    if block:
                        self.wfile.write(block)
                        self.wfile.flush()
            except (ValueError, json.JSONDecodeError):
                self.send_error(400, 'Invalid designated-model request')
            except (requests.RequestException, BrokenPipeError, ConnectionResetError):
                self.close_connection = True
            finally:
                if response is not None:
                    response.close()

    return Handler
