import ssl

import httpcore
import httpx
import pytest  # noqa
from yarl import URL  # noqa

from httpx_socks import (
    ProxyType,
    SyncProxyTransport,
    ProxyError,
    ProxyConnectionError,
    ProxyTimeoutError,
)
from tests.config import (
    TEST_HOST_PEM_FILE, TEST_URL_IPV4, TEST_URL_IPV4_HTTPS, SOCKS5_IPV4_URL,
    LOGIN, PASSWORD, PROXY_HOST_IPV4, SOCKS5_PROXY_PORT, TEST_URL_IPV4_DELAY,
    SKIP_IPV6_TESTS, SOCKS5_IPV6_URL, SOCKS4_URL, HTTP_PROXY_URL,
)


def create_ssl_context(url):
    parsed_url = URL(url)
    if parsed_url.scheme == 'https':
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(TEST_HOST_PEM_FILE)
        return ssl_context
    else:
        return None


def fetch(
        transport: SyncProxyTransport,
        url: str,
        timeout: httpx.Timeout = None,
):
    with httpx.Client(transport=transport) as client:  # type: ignore
        res = client.get(url=url, timeout=timeout)
        return res


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
def test_socks5_proxy_ipv4(url, rdns):
    transport = SyncProxyTransport.from_url(
        SOCKS5_IPV4_URL,
        rdns=rdns,
        verify=create_ssl_context(url)
    )
    res = fetch(transport=transport, url=url)
    assert res.status_code == 200


def test_socks5_proxy_with_invalid_credentials(url=TEST_URL_IPV4):
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
        verify=create_ssl_context(url)
    )
    with pytest.raises(ProxyError):
        fetch(transport=transport, url=url)


def test_socks5_proxy_with_read_timeout(url=TEST_URL_IPV4_DELAY):
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD,
        verify=create_ssl_context(url)
    )
    timeout = httpx.Timeout(2, connect=32)
    with pytest.raises(httpcore.ReadTimeout):
        fetch(transport=transport, url=url, timeout=timeout)


def test_socks5_proxy_with_connect_timeout(url=TEST_URL_IPV4):
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD,
        verify=create_ssl_context(url)
    )
    timeout = httpx.Timeout(32, connect=0.001)
    with pytest.raises(ProxyTimeoutError):
        fetch(transport=transport, url=url, timeout=timeout)


def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port,
                                              url=TEST_URL_IPV4):
    transport = SyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
        verify=create_ssl_context(url)
    )
    with pytest.raises(ProxyConnectionError):
        fetch(transport=transport, url=url)


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.skipif(SKIP_IPV6_TESTS, reason="TravisCI doesn't support ipv6")
def test_socks5_proxy_ipv6(url):
    transport = SyncProxyTransport.from_url(
        SOCKS5_IPV6_URL,
        verify=create_ssl_context(url)
    )
    res = fetch(transport=transport, url=url)
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
def test_socks4_proxy(url, rdns):
    transport = SyncProxyTransport.from_url(
        SOCKS4_URL, rdns=rdns,
        verify=create_ssl_context(url)
    )
    res = fetch(transport=transport, url=url)
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
def test_http_proxy(url):
    transport = SyncProxyTransport.from_url(
        HTTP_PROXY_URL,
        verify=create_ssl_context(url)
    )
    res = fetch(transport=transport, url=url)
    assert res.status_code == 200
