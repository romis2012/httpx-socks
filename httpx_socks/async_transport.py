import asyncio

from httpcore import AsyncConnectionPool
from httpcore._async.connection import AsyncHTTPConnection  # noqa
from httpcore._backends.asyncio import (SocketStream  # noqa
                                        as AsyncioSocketStream)
from httpcore._utils import url_to_origin  # noqa
from httpx._config import SSLConfig  # noqa

from .proxy import ProxyType, parse_proxy_url
from .proxy.aio import create_proxy


class AsyncProxyTransport(AsyncConnectionPool):
    def __init__(self, *, proxy_type: ProxyType,
                 proxy_host: str, proxy_port: int,
                 username=None, password=None, rdns=None,
                 http2=False, ssl_context=None, verify=True, cert=None,
                 trust_env=True,
                 loop=None):

        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._proxy_type = proxy_type
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._username = username
        self._password = password
        self._rdns = rdns

        if ssl_context is None:
            ssl_context = SSLConfig(
                verify=verify, cert=cert,
                trust_env=trust_env, http2=http2
            ).ssl_context

        self.ssl_context = ssl_context
        self.http2 = http2

        super().__init__(http2=http2, ssl_context=ssl_context)

    async def request(self, method, url, headers=None, stream=None,
                      timeout=None):

        origin = url_to_origin(url)
        connection = await self._get_connection_from_pool(origin)

        if connection is None:
            socket = await self._connect_to_proxy(origin=origin,
                                                  timeout=timeout)
            connection = AsyncHTTPConnection(
                origin=origin,
                http2=self.http2,
                ssl_context=self.ssl_context,
                socket=socket
            )
            await self._add_to_pool(connection)

        response = await connection.request(method, url, headers, stream,
                                            timeout)
        return response

    async def _connect_to_proxy(self, origin, timeout):
        scheme, hostname, port = origin

        ssl_context = self.ssl_context if scheme == b'https' else None
        host = hostname.decode('ascii')  # ?

        timeout = {} if timeout is None else timeout
        connect_timeout = timeout.get('connect')

        proxy = create_proxy(
            loop=self._loop,
            proxy_type=self._proxy_type,
            host=self._proxy_host, port=self._proxy_port,
            username=self._username, password=self._password,
            rdns=self._rdns
        )

        await proxy.connect(host, port, timeout=connect_timeout)
        # noinspection PyTypeChecker
        stream_reader, stream_writer = await asyncio.open_connection(
            loop=self._loop,
            host=None,
            port=None,
            sock=proxy.socket,
            ssl=ssl_context,
            server_hostname=host if ssl_context else None,
        )
        return AsyncioSocketStream(
            stream_reader=stream_reader, stream_writer=stream_writer
        )

    @classmethod
    def from_url(cls, url, **kwargs):
        proxy_type, host, port, username, password = parse_proxy_url(url)
        return cls(
            proxy_type=proxy_type,
            proxy_host=host,
            proxy_port=port,
            username=username,
            password=password,
            **kwargs
        )
