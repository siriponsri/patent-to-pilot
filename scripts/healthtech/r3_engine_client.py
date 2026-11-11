"""Bounded local Docker Engine transport; no shell or remote network endpoint.

The socket stays on the controller host, never in a research container.
Reference: https://docs.docker.com/reference/api/engine/version/v1.47/
"""
import http.client
import json
import socket


class EngineError(RuntimeError):
    def __init__(self, status):
        super().__init__(f'engine HTTP status {status}')
        self.status = status


class UnixConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect('/var/run/docker.sock')


class Engine:
    def __init__(self, connection=UnixConnection):
        self.connection = connection

    def request(self, method, path, payload=None, *, timeout=10):
        if method not in {'GET', 'POST'} or not path.startswith('/') or timeout > 15:
            raise ValueError('invalid bounded Engine request')
        body = None if payload is None else json.dumps(payload).encode()
        connection = self.connection('localhost', timeout=timeout)
        try:
            connection.request(method, path, body=body,
                               headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            raw = response.read(4*1024*1024+1)
            if len(raw) > 4*1024*1024:
                raise RuntimeError('Engine response cap exceeded')
            if response.status >= 400:
                raise EngineError(response.status)
            return json.loads(raw) if raw else None
        finally:
            connection.close()

    def check_version(self):
        value = self.request('GET', '/version')
        pair = lambda v: tuple(int(part) for part in v.split('.'))
        if not pair(value['MinAPIVersion']) <= (1, 47) <= pair(value['ApiVersion']):
            raise RuntimeError('Engine API 1.47 unavailable')
        return {key: value[key] for key in ('Version', 'ApiVersion', 'MinAPIVersion')}

    def inspect(self, name):
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in name):
            raise ValueError('invalid owned container name')
        return self.request('GET', '/v1.47/containers/'+name+'/json')

    def terminate(self, name):
        try:
            self.request('POST', '/v1.47/containers/'+name+'/stop?t=5', timeout=15)
        except (OSError, http.client.HTTPException, EngineError):
            pass
        try:
            state = self.inspect(name)
        except (OSError, http.client.HTTPException, EngineError):
            state = None
        if state is None or state['State']['Running']:
            try:
                self.request('POST', '/v1.47/containers/'+name+'/kill')
            except (OSError, http.client.HTTPException, EngineError):
                pass
            state = self.inspect(name)
        if state['State']['Running']:
            raise RuntimeError('owned termination unknown')
        return state
