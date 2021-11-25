import ssl

import httpcore
import httpx
import pytest
from yarl import URL

from httpx_socks import (
    ProxyType,
    SyncProxyTransport,
    ProxyError,
    ProxyConnectionError,
    ProxyTimeoutError,
)

from httpx_socks._sync_proxy import SyncProxy
from tests.config import (
    TEST_HOST_PEM_FILE, TEST_URL_IPV4, TEST_URL_IPV4_HTTPS, SOCKS5_IPV4_URL,
    LOGIN, PASSWORD, PROXY_HOST_IPV4, SOCKS5_PROXY_PORT, TEST_URL_IPV4_DELAY,
    SKIP_IPV6_TESTS, SOCKS5_IPV6_URL, SOCKS4_URL, HTTP_PROXY_URL, SOCKS5_IPV4_HOSTNAME_URL,
)


def create_ssl_context(url, http2=False):
    parsed_url = URL(url)
    if parsed_url.scheme == 'https':
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(TEST_HOST_PEM_FILE)
        alpn_protocols = ['http/1.1', 'h2'] if http2 else ['http/1.1']
        ssl_context.set_alpn_protocols(alpn_protocols)
        return ssl_context
    else:
        return None


def fetch(transport: SyncProxyTransport, url: str, timeout: httpx.Timeout = None):
    with httpx.Client(transport=transport) as client:  # type: ignore
        res = client.get(url=url, timeout=timeout)
        return res


@pytest.mark.parametrize('proxy_url', (SOCKS5_IPV4_URL, SOCKS5_IPV4_HOSTNAME_URL, HTTP_PROXY_URL))
@pytest.mark.parametrize('target_url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
def test_proxy_direct(proxy_url, target_url):
    with SyncProxy.from_url(proxy_url, ssl_context=create_ssl_context(target_url)) as proxy:
        res = proxy.request(method="GET", url=target_url)
        assert res.status == 200
        res = proxy.request(method="GET", url=target_url)
        assert res.status == 200


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


def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port, url=TEST_URL_IPV4):
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


def test_proxy_http2():
    url = TEST_URL_IPV4_HTTPS
    proxy_url = HTTP_PROXY_URL
    ssl_context = create_ssl_context(url, http2=True)

    transport = SyncProxyTransport.from_url(proxy_url, verify=ssl_context, http2=True)
    res = fetch(transport=transport, url=url)
    assert res.status_code == 200
    assert res.http_version == 'HTTP/2'
