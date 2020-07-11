import warnings

import trio.socket

from .abc import AbstractProxy
from .mixins import StreamSocketReadWriteMixin, ResolveMixin
from ..errors import ProxyConnectionError, ProxyTimeoutError
from ..helpers import is_ipv4_address, is_ipv6_address


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
        self._timeout = None
        self._socket = None

    async def connect(self, dest_host, dest_port, timeout=None, _socket=None):
        self._dest_host = dest_host
        self._dest_port = dest_port
        self._timeout = timeout

        try:
            await self._connect(_socket=_socket)
        except trio.TooSlowError as e:
            await self._close()
            raise ProxyTimeoutError('Proxy connection timed out: %s'
                                    % self._timeout) from e
        except Exception:
            await self._close()
            raise

    async def negotiate(self):  # pragma: no cover
        raise NotImplementedError()

    async def _connect(self, _socket=None):
        with trio.fail_after(self._timeout):
            if _socket is None:
                proxy_family, proxy_host = await self._resolve_proxy_host()

                self._socket = trio.socket.socket(
                    family=proxy_family,
                    type=trio.socket.SOCK_STREAM
                )

                await self._connect_to_proxy(
                    host=proxy_host,
                    port=self._proxy_port
                )
            else:
                self._socket = _socket

            await self.negotiate()

    async def _connect_to_proxy(self, host, port):
        try:
            await self._socket.connect((host, port))
        except OSError as e:
            msg = 'Can not connect to proxy {}:{} [{}]'.format(
                host, port, e.strerror)
            raise ProxyConnectionError(e.errno, msg) from e

    async def _resolve_proxy_host(self):
        host = self._proxy_host
        if is_ipv4_address(host):
            return trio.socket.AF_INET, host
        if is_ipv6_address(host):
            return trio.socket.AF_INET6, host
        return await self.resolve(host=host)

    async def _close(self):
        if self._socket is not None:
            self._socket.close()
            await trio.lowlevel.checkpoint()

    @property
    def socket(self):
        return self._socket

    @property
    def host(self):
        return self._proxy_host

    @property
    def port(self):
        return self._proxy_port
