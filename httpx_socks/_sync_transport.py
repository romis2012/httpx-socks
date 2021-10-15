import httpcore
from httpcore._backends.sync import SyncSocketStream  # noqa
from httpcore._sync.connection import SyncHTTPConnection  # noqa
from httpcore._utils import url_to_origin  # noqa

from httpx import BaseTransport, Request, Response, SyncByteStream
from httpx._config import SSLConfig, DEFAULT_LIMITS, create_ssl_context  # noqa

from python_socks import ProxyType, parse_proxy_url
from python_socks.sync import Proxy


class ResponseStream(SyncByteStream):
    def __init__(self, httpcore_stream: httpcore.SyncByteStream):
        self._httpcore_stream = httpcore_stream

    def __iter__(self):
        for part in self._httpcore_stream:
            yield part

    def close(self) -> None:
        self._httpcore_stream.close()


class SyncProxyTransport(BaseTransport):
    def __init__(
            self,
            *,
            proxy_type: ProxyType,
            proxy_host: str,
            proxy_port: int,
            username=None,
            password=None,
            rdns=None,

            verify=True,
            cert=None,
            trust_env: bool = True,
            **kwargs
    ):
        ssl_context = create_ssl_context(
            verify=verify,
            cert=cert,
            trust_env=trust_env,
        )

        self._pool = SyncProxy(
            proxy_type=proxy_type,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            username=username,
            password=password,
            rdns=rdns,
            ssl_context=ssl_context,
            **kwargs
        )

    def handle_request(self, request: Request) -> Response:
        (
            status_code,
            headers,
            byte_stream,
            extensions
        ) = self._pool.handle_request(
            method=request.method.encode("ascii"),
            url=request.url.raw,
            headers=request.headers.raw,
            stream=httpcore.IteratorByteStream(iter(request.stream)),
            extensions=request.extensions,
        )

        return Response(
            status_code,
            headers=headers,
            stream=ResponseStream(byte_stream),
            extensions=extensions
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

    def close(self) -> None:
        self._pool.close()  # pragma: no cover

    def __enter__(self):
        self._pool.__enter__()
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self._pool.__exit__(exc_type, exc_value, traceback)


class SyncProxy(httpcore.SyncConnectionPool):
    def __init__(
            self,
            *,
            proxy_type: ProxyType,
            proxy_host: str,
            proxy_port: int,
            username=None,
            password=None,
            rdns=None,
            **kwargs
    ):

        self._proxy_type = proxy_type
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._username = username
        self._password = password
        self._rdns = rdns

        super().__init__(**kwargs)

    def handle_request(self, method, url, headers=None, stream=None,
                       extensions=None):
        origin = url_to_origin(url)
        connection = self._get_connection_from_pool(origin)

        extensions = {} if extensions is None else extensions
        timeout = extensions.get('timeout', {})
        connect_timeout = timeout.get('connect')

        if connection is None:
            socket = self._connect_via_proxy(
                origin=origin,
                connect_timeout=connect_timeout
            )
            connection = SyncHTTPConnection(
                origin=origin,
                http1=self._http1,
                http2=self._http2,
                keepalive_expiry=self._keepalive_expiry,
                uds=self._uds,
                local_address=self._local_address,
                retries=self._retries,
                ssl_context=self._ssl_context,
                socket=socket,
            )
            self._add_to_pool(connection=connection, timeout=timeout)

        response = connection.handle_request(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            extensions=extensions
        )

        return response

    def _connect_via_proxy(self, origin, connect_timeout):
        scheme, hostname, port = origin

        ssl_context = self._ssl_context if scheme == b'https' else None
        host = hostname.decode('ascii')  # ?

        proxy = Proxy.create(
            proxy_type=self._proxy_type,
            host=self._proxy_host,
            port=self._proxy_port,
            username=self._username,
            password=self._password,
            rdns=self._rdns
        )

        sock = proxy.connect(host, port, timeout=connect_timeout)

        if ssl_context is not None:
            sock = ssl_context.wrap_socket(
                sock, server_hostname=host
            )
        return SyncSocketStream(sock=sock)
