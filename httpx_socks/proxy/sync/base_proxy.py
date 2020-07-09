import socket
import warnings

from ..errors import ProxyConnectionError, ProxyTimeoutError
from ..helpers import is_ipv4_address, is_ipv6_address
from .abc import AbstractProxy
from .mixins import StreamSocketReadWriteMixin, ResolveMixin


class BaseProxy(AbstractProxy, StreamSocketReadWriteMixin, ResolveMixin):
    def __init__(self, proxy_host, proxy_port, family=None):
        if family is not None:
            warnings.warn('Parameter family is deprecated '
                          'and will be ignored.', DeprecationWarning,
                          stacklevel=2)

        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._dest_host = None
        self._dest_port = None

    def connect(self, dest_host, dest_port, timeout=None, _socket=None):
        self._dest_host = dest_host
        self._dest_port = dest_port

        if _socket is None:
            proxy_family, proxy_host = self._resolve_proxy_host()

            self._socket = socket.socket(
                family=proxy_family,
                type=socket.SOCK_STREAM
            )

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._connect_to_proxy(
                host=proxy_host,
                port=self._proxy_port
            )
        else:
            self._socket = _socket

        try:
            self.negotiate()
        except socket.timeout:
            self.close()
            raise ProxyTimeoutError('Proxy connection timed out')
        except Exception:
            self.close()
            raise

    def negotiate(self):  # pragma: no cover
        raise NotImplementedError()

    def _connect_to_proxy(self, host, port):
        try:
            self._socket.connect((host, port))
        except OSError as e:
            self.close()
            msg = 'Can not connect to proxy {}:{} [{}]'.format(
                host, port, e.strerror)
            raise ProxyConnectionError(e.errno, msg) from e

    def _resolve_proxy_host(self):
        host = self._proxy_host
        if is_ipv4_address(host):
            return socket.AF_INET, host
        if is_ipv6_address(host):
            return socket.AF_INET6, host
        return self.resolve(host=host)

    def close(self):
        self._socket.close()

    @property
    def socket(self):
        return self._socket

    @property
    def host(self):
        return self._proxy_host

    @property
    def port(self):
        return self._proxy_port
