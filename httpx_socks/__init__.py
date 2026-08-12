__title__ = "httpx-socks"
__version__ = "0.12.0"

from python_socks import (
    ProxyConnectionError,
    ProxyError,
    ProxyTimeoutError,
    ProxyType,
)

from ._async_transport import AsyncProxyTransport
from ._sync_transport import SyncProxyTransport

__all__ = (
    "AsyncProxyTransport",
    "ProxyConnectionError",
    "ProxyError",
    "ProxyTimeoutError",
    "ProxyType",
    "SyncProxyTransport",
    "__title__",
    "__version__",
)
