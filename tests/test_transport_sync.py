import httpx
import pytest  # noqa

from httpx_socks import (
    ProxyType,
    SyncProxyTransport,
    ProxyError,
    ProxyConnectionError,
    ProxyTimeoutError,
)
from tests.conftest import (
    SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT,
    LOGIN, PASSWORD, SKIP_IPV6_TESTS, SOCKS5_IPV4_URL, SOCKS5_IPV6_URL,
    SOCKS4_URL,
    HTTP_PROXY_URL)

# HTTP_TEST_URL = 'http://httpbin.org/ip'
# HTTPS_TEST_URL = 'https://httpbin.org/ip'
HTTP_TEST_URL = 'http://check-host.net/ip'
HTTPS_TEST_URL = 'https://check-host.net/ip'

HTTP_URL_DELAY_3_SEC = 'http://httpbin.org/delay/3'
HTTP_URL_REDIRECT = 'http://httpbin.org/redirect/1'


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
    timeout = httpx.Timeout(2, connect=32)
    with pytest.raises(httpx.ReadTimeout):
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
    timeout = httpx.Timeout(32, connect=0.001)
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
