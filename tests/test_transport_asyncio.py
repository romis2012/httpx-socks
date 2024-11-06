import ssl
from unittest import mock

import httpx
import pytest
from yarl import URL

from httpx_socks import (
    ProxyType,
    AsyncProxyTransport,
    ProxyError,
    ProxyConnectionError,
    ProxyTimeoutError,
)
from httpx_socks._async_proxy import AsyncProxy
from tests.config import (
    TEST_URL_IPV4,
    TEST_URL_IPV4_HTTPS,
    SOCKS5_IPV4_URL,
    LOGIN,
    PASSWORD,
    PROXY_HOST_IPV4,
    SOCKS5_PROXY_PORT,
    TEST_URL_IPV4_DELAY,
    SKIP_IPV6_TESTS,
    SOCKS5_IPV6_URL,
    SOCKS4_URL,
    HTTP_PROXY_URL,
    SOCKS5_IPV4_HOSTNAME_URL,
    HTTPS_PROXY_URL,
)


def create_ssl_context(url, ca, http2=False):
    parsed_url = URL(url)
    if parsed_url.scheme == 'https':
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        # ssl_context.load_verify_locations(TEST_HOST_PEM_FILE)
        alpn_protocols = ['http/1.1', 'h2'] if http2 else ['http/1.1']
        ssl_context.set_alpn_protocols(alpn_protocols)
        ca.configure_trust(ssl_context)
        return ssl_context
    else:
        return None


async def fetch(
    transport: AsyncProxyTransport,
    url: str,
    timeout: httpx.Timeout = None,
):
    async with httpx.AsyncClient(transport=transport) as client:
        res = await client.get(url=url, timeout=timeout)
        return res


@pytest.mark.parametrize('proxy_url', (SOCKS5_IPV4_URL, SOCKS5_IPV4_HOSTNAME_URL, HTTP_PROXY_URL))
@pytest.mark.parametrize('target_url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.asyncio
async def test_proxy_direct(proxy_url, target_url, target_ssl_ca):
    ssl_context = create_ssl_context(url=target_url, ca=target_ssl_ca)
    async with AsyncProxy.from_url(proxy_url, ssl_context=ssl_context) as proxy:
        res = await proxy.request(method="GET", url=target_url)
        assert res.status == 200
        res = await proxy.request(method="GET", url=target_url)
        assert res.status == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks5_proxy_ipv4(url, rdns, target_ssl_ca):
    transport = AsyncProxyTransport.from_url(
        SOCKS5_IPV4_URL, rdns=rdns, verify=create_ssl_context(url, ca=target_ssl_ca)
    )
    res = await fetch(transport=transport, url=url)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_credentials(target_ssl_ca, url=TEST_URL_IPV4):
    transport = AsyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD + 'aaa',
        verify=create_ssl_context(url, ca=target_ssl_ca),
    )
    with pytest.raises(ProxyError):
        await fetch(transport=transport, url=url)


@pytest.mark.asyncio
async def test_socks5_proxy_with_read_timeout(target_ssl_ca, url=TEST_URL_IPV4_DELAY):
    transport = AsyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD,
        verify=create_ssl_context(url, ca=target_ssl_ca),
    )
    timeout = httpx.Timeout(2, connect=32)
    # with pytest.raises(httpcore.ReadTimeout):
    with pytest.raises(httpx.ReadTimeout):
        await fetch(transport=transport, url=url, timeout=timeout)


@pytest.mark.asyncio
async def test_socks5_proxy_with_connect_timeout(target_ssl_ca, url=TEST_URL_IPV4):
    transport = AsyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=SOCKS5_PROXY_PORT,
        username=LOGIN,
        password=PASSWORD,
        verify=create_ssl_context(url, ca=target_ssl_ca),
    )
    timeout = httpx.Timeout(32, connect=0.001)
    with pytest.raises(ProxyTimeoutError):
        await fetch(transport=transport, url=url, timeout=timeout)


@pytest.mark.asyncio
async def test_socks5_proxy_with_invalid_proxy_port(
    unused_tcp_port,
    target_ssl_ca,
    url=TEST_URL_IPV4,
):
    transport = AsyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=PROXY_HOST_IPV4,
        proxy_port=unused_tcp_port,
        username=LOGIN,
        password=PASSWORD,
        verify=create_ssl_context(url, ca=target_ssl_ca),
    )
    with pytest.raises(ProxyConnectionError):
        await fetch(transport=transport, url=url)


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.skipif(SKIP_IPV6_TESTS, reason="TravisCI doesn't support ipv6")
@pytest.mark.asyncio
async def test_socks5_proxy_ipv6(url, target_ssl_ca):
    transport = AsyncProxyTransport.from_url(
        SOCKS5_IPV6_URL, verify=create_ssl_context(url, ca=target_ssl_ca)
    )
    res = await fetch(transport=transport, url=url)
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.asyncio
async def test_socks4_proxy(url, rdns, target_ssl_ca):
    transport = AsyncProxyTransport.from_url(
        SOCKS4_URL, rdns=rdns, verify=create_ssl_context(url, ca=target_ssl_ca)
    )
    res = await fetch(transport=transport, url=url)
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.asyncio
async def test_http_proxy(url, target_ssl_ca):
    transport = AsyncProxyTransport.from_url(
        HTTP_PROXY_URL, verify=create_ssl_context(url, ca=target_ssl_ca)
    )
    res = await fetch(transport=transport, url=url)
    assert res.status_code == 200


@pytest.mark.parametrize('url', (TEST_URL_IPV4, TEST_URL_IPV4_HTTPS))
@pytest.mark.parametrize('http2', (False, True))
@pytest.mark.asyncio
async def test_secure_proxy(url, http2, proxy_ssl_context, target_ssl_ca):
    transport = AsyncProxyTransport.from_url(
        HTTPS_PROXY_URL,
        proxy_ssl=proxy_ssl_context,
        http2=http2,
        verify=create_ssl_context(url, ca=target_ssl_ca, http2=http2),
    )
    res = await fetch(transport=transport, url=url)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_proxy_http2(target_ssl_ca):
    url = TEST_URL_IPV4_HTTPS
    proxy_url = HTTP_PROXY_URL
    ssl_context = create_ssl_context(url, ca=target_ssl_ca, http2=True)

    transport = AsyncProxyTransport.from_url(proxy_url, verify=ssl_context, http2=True)
    res = await fetch(transport=transport, url=url)
    assert res.status_code == 200
    assert res.http_version == 'HTTP/2'


@pytest.mark.asyncio
async def test_failed_proxy_connection():
    url = TEST_URL_IPV4_HTTPS
    proxy_url = HTTP_PROXY_URL

    transport = AsyncProxyTransport.from_url(proxy_url)
    async with httpx.AsyncClient(transport=transport) as client:
        with mock.patch(
            'httpx_socks._async_proxy.AsyncProxyConnection._connect_via_proxy',
            new=mock.AsyncMock(side_effect=Exception),
        ):
            with pytest.raises(Exception):
                await client.get(url=url)

        assert len(client._transport._pool._connections) == 0
