import ssl
import typing

from httpcore._backends.sync import SyncStream as CoreSyncStream
from httpcore._utils import is_socket_readable
from python_socks.sync.v2._ssl_transport import SSLTransport


class SyncStream(CoreSyncStream):
    def get_extra_info(self, info: str) -> typing.Any:  # noqa: C901, PLR0911, PLR0912
        if info == "ssl_object":
            if isinstance(self._sock, ssl.SSLSocket):
                return self._sock._sslobj  # type: ignore[attr-defined]  # noqa: SLF001
            if isinstance(self._sock, SSLTransport):
                return self._sock.sslobj
            return None

        if info == "client_addr":  # pragma: nocover
            if isinstance(self._sock, SSLTransport):
                return self._sock.socket.getsockname()
            else:  # noqa: RET505
                return self._sock.getsockname()

        if info == "server_addr":  # pragma: nocover
            if isinstance(self._sock, SSLTransport):
                return self._sock.socket.getpeername()
            else:  # noqa: RET505
                return self._sock.getpeername()

        if info == "socket":  # pragma: nocover
            return self._sock  # ???

        if info == "is_readable":
            if isinstance(self._sock, SSLTransport):
                return is_socket_readable(self._sock.socket)
            else:  # noqa: RET505
                return is_socket_readable(self._sock)

        return None  # pragma: nocover
