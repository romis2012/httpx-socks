from ..enums import ProxyType
from .http_proxy import HttpProxy
from .socks4_proxy import Socks4Proxy
from .socks5_proxy import Socks5Proxy


def create_proxy(proxy_type, host, port, username=None, password=None,
                 rdns=None, family=None):

    if proxy_type == ProxyType.SOCKS4:
        return Socks4Proxy(
            proxy_host=host, proxy_port=port,
            user_id=username, rdns=rdns)

    if proxy_type == ProxyType.SOCKS5:
        return Socks5Proxy(
            proxy_host=host, proxy_port=port,
            username=username, password=password, rdns=rdns, family=family)

    if proxy_type == ProxyType.HTTP:
        return HttpProxy(
            proxy_host=host, proxy_port=port,
            username=username, password=password)

    raise ValueError(
        'Invalid proxy type: {}'.format(proxy_type))  # pragma: no cover
