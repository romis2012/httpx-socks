import sniffio

from httpcore import AsyncConnectionPool
from httpcore._async.connection import AsyncHTTPConnection  # noqa
from httpcore._utils import url_to_origin  # noqa
from httpx._config import SSLConfig  # noqa

from python_socks import ProxyType, parse_proxy_url


class AsyncProxyTransport(AsyncConnectionPool):
    def __init__(self, *, proxy_type: ProxyType,
                 proxy_host: str, proxy_port: int,
                 username=None, password=None, rdns=None,
                 http2=False, ssl_context=None, verify=True, cert=None,
                 trust_env=True,
                 loop=None, **kwargs):

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

        super().__init__(http2=http2, ssl_context=ssl_context, **kwargs)

    async def arequest(self, method, url, headers=None, stream=None,
                       ext=None):

        origin = url_to_origin(url)
        connection = await self._get_connection_from_pool(origin)

        ext = {} if ext is None else ext
        timeout = ext.get('timeout', {})
        connect_timeout = timeout.get('connect')

        if connection is None:
            socket = await self._connect_to_proxy(
                origin=origin,
                connect_timeout=connect_timeout
            )
            connection = AsyncHTTPConnection(
                origin=origin,
                http2=self._http2,
                ssl_context=self._ssl_context,
                socket=socket
            )
            await self._add_to_pool(connection=connection, timeout=timeout)

        response = await connection.arequest(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            ext=ext
        )
        return response

    async def _connect_to_proxy(self, origin, connect_timeout):
        scheme, hostname, port = origin

        ssl_context = self._ssl_context if scheme == b'https' else None
        host = hostname.decode('ascii')  # ?

        return await self._open_stream(
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            ssl_context=ssl_context
        )

    async def _open_stream(self, host, port, connect_timeout, ssl_context):
        backend = sniffio.current_async_library()

        if backend == 'asyncio':
            return await self._open_aio_stream(
                host,
                port,
                connect_timeout,
                ssl_context
            )

        if backend == 'trio':
            return await self._open_trio_stream(
                host,
                port,
                connect_timeout,
                ssl_context
            )

        if backend == 'curio':
            return await self._open_curio_stream(
                host,
                port,
                connect_timeout,
                ssl_context
            )

        raise RuntimeError(f'Unsupported '  # pragma: no cover
                           f'concurrency backend {backend!r}')

    async def _open_aio_stream(self, host, port, connect_timeout,
                               ssl_context):
        import asyncio
        from httpcore._backends.asyncio import SocketStream  # noqa
        from python_socks.async_.asyncio import Proxy

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        proxy = Proxy.create(
            loop=self._loop,
            proxy_type=self._proxy_type,
            host=self._proxy_host,
            port=self._proxy_port,
            username=self._username,
            password=self._password,
            rdns=self._rdns
        )

        sock = await proxy.connect(host, port, timeout=connect_timeout)

        stream_reader, stream_writer = await asyncio.open_connection(
            host=None,
            port=None,
            sock=sock,
            ssl=ssl_context,
            server_hostname=host if ssl_context else None,
        )
        return SocketStream(
            stream_reader=stream_reader, stream_writer=stream_writer
        )

    async def _open_trio_stream(self, host, port, connect_timeout,
                                ssl_context):
        import trio
        from httpcore._backends.trio import SocketStream  # noqa
        from python_socks.async_.trio import Proxy

        proxy = Proxy.create(
            proxy_type=self._proxy_type,
            host=self._proxy_host,
            port=self._proxy_port,
            username=self._username,
            password=self._password,
            rdns=self._rdns
        )

        sock = await proxy.connect(host, port, timeout=connect_timeout)

        stream = trio.SocketStream(sock)

        if ssl_context is not None:
            stream = trio.SSLStream(
                stream, ssl_context,
                server_hostname=host
            )
            await stream.do_handshake()

        return SocketStream(
            stream=stream
        )

    async def _open_curio_stream(self, host, port, connect_timeout,
                                 ssl_context):
        import curio.io
        from httpcore._backends.curio import SocketStream  # noqa
        from python_socks.async_.curio import Proxy

        proxy = Proxy.create(
            proxy_type=self._proxy_type,
            host=self._proxy_host,
            port=self._proxy_port,
            username=self._username,
            password=self._password,
            rdns=self._rdns
        )

        sock = await proxy.connect(host, port, timeout=connect_timeout)

        if ssl_context is not None:
            sock = curio.io.Socket(
                ssl_context.wrap_socket(
                    sock._socket,  # noqa
                    do_handshake_on_connect=False,
                    server_hostname=host
                )
            )
            await sock.do_handshake()

        return SocketStream(
            socket=sock
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
