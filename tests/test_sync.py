import httpcore
import httpx
# noinspection PyPackageRequirements
import pytest

from httpx_socks import (
    ProxyType,
    SyncProxyTransport,
    ProxyError,
    ProxyConnectionError,
    ProxyTimeoutError,
)
from tests.conftest import (
    SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT,
    LOGIN, PASSWORD, SOCKS5_IPV6_HOST,
    SOCKS5_IPV6_PORT, SOCKS4_HOST, SOCKS4_PORT,
    HTTP_PROXY_HOST, HTTP_PROXY_PORT,
    SKIP_IPV6_TESTS)

HTTP_TEST_HOST = 'httpbin.org'
HTTP_TEST_PORT = 80

HTTPS_TEST_HOST = 'httpbin.org'
HTTPS_TEST_PORT = 443

HTTP_TEST_URL = 'http://%s/ip' % HTTP_TEST_HOST
HTTPS_TEST_URL = 'https://%s/ip' % HTTP_TEST_HOST

HTTP_URL_DELAY_3_SEC = 'http://httpbin.org/delay/3'
HTTP_URL_REDIRECT = 'http://httpbin.org/redirect/1'

SOCKS5_IPV4_URL = 'socks5://{LOGIN}:{PASSWORD}@{SOCKS5_IPV4_HOST}:{SOCKS5_IPV4_PORT}'.format(  # noqa
    SOCKS5_IPV4_HOST=SOCKS5_IPV4_HOST,
    SOCKS5_IPV4_PORT=SOCKS5_IPV4_PORT,
    LOGIN=LOGIN,
    PASSWORD=PASSWORD,
)

SOCKS5_IPV6_URL = 'socks5://{LOGIN}:{PASSWORD}@{SOCKS5_IPV6_HOST}:{SOCKS5_IPV6_PORT}'.format(  # noqa
    SOCKS5_IPV6_HOST='[%s]' % SOCKS5_IPV6_HOST,
    SOCKS5_IPV6_PORT=SOCKS5_IPV6_PORT,
    LOGIN=LOGIN,
    PASSWORD=PASSWORD,
)

SOCKS4_URL = 'socks4://{SOCKS4_HOST}:{SOCKS4_PORT}'.format(
    SOCKS4_HOST=SOCKS4_HOST,
    SOCKS4_PORT=SOCKS4_PORT,
)

HTTP_PROXY_URL = 'http://{LOGIN}:{PASSWORD}@{HTTP_PROXY_HOST}:{HTTP_PROXY_PORT}'.format(  # noqa
    HTTP_PROXY_HOST=HTTP_PROXY_HOST,
    HTTP_PROXY_PORT=HTTP_PROXY_PORT,
    LOGIN=LOGIN,
    PASSWORD=PASSWORD,
)


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
def test_socks5_proxy_ipv4(url, rdns):
    transport = SyncProxyTransport.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    with httpx.Client(transport=transport) as client:
        resp = client.get(url)
        assert resp.status_code == 200


def test_socks5_proxy_with_invalid_credentials():
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=SOCKS5_IPV4_HOST,
        proxy_port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
    )
    with pytest.raises(ProxyError):
        with httpx.Client(transport=transport) as client:
            client.get(HTTP_TEST_URL)


def test_socks5_proxy_with_read_timeout():
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=SOCKS5_IPV4_HOST,
        proxy_port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    timeout = httpx.Timeout(2, connect_timeout=32)
    with pytest.raises(httpcore.ReadTimeout):
        with httpx.Client(transport=transport, timeout=timeout) as client:
            client.get(HTTP_URL_DELAY_3_SEC)


def test_socks5_proxy_with_connect_timeout():
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=SOCKS5_IPV4_HOST,
        proxy_port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    timeout = httpx.Timeout(32, connect_timeout=0.001)
    with pytest.raises(ProxyTimeoutError):
        with httpx.Client(transport=transport, timeout=timeout) as client:
            client.get(HTTP_TEST_URL)


def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port):
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=SOCKS5_IPV4_HOST,
        proxy_port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
    )
    with pytest.raises(ProxyConnectionError):
        with httpx.Client(transport=transport) as client:
            client.get(HTTP_TEST_URL)


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
def test_socks5_proxy_ipv6():
    transport = SyncProxyTransport.from_url(SOCKS5_IPV6_URL)
    with httpx.Client(transport=transport) as client:
        resp = client.get(HTTP_TEST_URL)
        assert resp.status_code == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
def test_socks4_proxy(url, rdns):
    transport = SyncProxyTransport.from_url(SOCKS4_URL, rdns=rdns, )
    with httpx.Client(transport=transport) as client:
        resp = client.get(url)
        assert resp.status_code == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
def test_http_proxy(url):
    transport = SyncProxyTransport.from_url(HTTP_PROXY_URL)
    with httpx.Client(transport=transport) as client:
        resp = client.get(url)
        assert resp.status_code == 200
