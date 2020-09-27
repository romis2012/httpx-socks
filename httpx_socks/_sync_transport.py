from httpcore import SyncConnectionPool
from httpcore._backends.sync import SyncSocketStream  # noqa
from httpcore._sync.connection import SyncHTTPConnection # noqa
from httpcore._utils import url_to_origin # noqa
from httpx._config import SSLConfig # noqa

from python_socks import ProxyType, parse_proxy_url
from python_socks.sync import Proxy


class SyncProxyTransport(SyncConnectionPool):
    def __init__(self, *, proxy_type: ProxyType,
                 proxy_host: str, proxy_port: int,
                 username=None, password=None, rdns=None,
                 http2=False, ssl_context=None, verify=True, cert=None,
                 trust_env=True, **kwargs):

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

    def request(self, method, url, headers=None, stream=None, ext=None):
        origin = url_to_origin(url)
        connection = self._get_connection_from_pool(origin)

        ext = {} if ext is None else ext
        timeout = ext.get('timeout', {})
        connect_timeout = timeout.get('connect')

        if connection is None:
            socket = self._connect_to_proxy(
                origin=origin,
                connect_timeout=connect_timeout
            )
            connection = SyncHTTPConnection(
                origin=origin,
                http2=self._http2,
                ssl_context=self._ssl_context,
                socket=socket,
            )
            self._add_to_pool(connection=connection, timeout=timeout)

        response = connection.request(
            method=method,
            url=url,
            headers=headers,
            stream=stream,
            ext=ext
        )

        return response

    def _connect_to_proxy(self, origin, connect_timeout):
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
