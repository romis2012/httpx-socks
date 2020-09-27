import curio
import httpx
import pytest  # noqa

from httpx_socks import (
    ProxyType,
    AsyncProxyTransport,
    ProxyError,
    ProxyConnectionError,
    ProxyTimeoutError,
)
from tests.conftest import (
    SOCKS5_IPV4_HOST, SOCKS5_IPV4_PORT,
    LOGIN, PASSWORD, SKIP_IPV6_TESTS, SOCKS5_IPV4_URL, SOCKS5_IPV6_URL,
    SOCKS4_URL, HTTP_PROXY_URL)


HTTP_TEST_URL = 'http://check-host.net/ip'
HTTPS_TEST_URL = 'https://check-host.net/ip'

HTTP_URL_DELAY_3_SEC = 'http://httpbin.org/delay/3'


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
def test_socks5_proxy_ipv4(url, rdns):
    async def main():
        transport = AsyncProxyTransport.from_url(SOCKS5_IPV4_URL, rdns=rdns)
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(url)
            assert resp.status_code == 200

    curio.run(main)


def test_socks5_proxy_with_invalid_credentials():
    async def main():
        transport = AsyncProxyTransport(
            proxy_type=ProxyType.SOCKS5,
            proxy_host=SOCKS5_IPV4_HOST,
            proxy_port=SOCKS5_IPV4_PORT,
            username=LOGIN,
            password=PASSWORD + 'aaa',
        )
        with pytest.raises(ProxyError):
            async with httpx.AsyncClient(transport=transport) as client:
                await client.get(HTTP_TEST_URL)

    curio.run(main)


def test_socks5_proxy_with_read_timeout():
    async def main():
        transport = AsyncProxyTransport(
            proxy_type=ProxyType.SOCKS5,
            proxy_host=SOCKS5_IPV4_HOST,
            proxy_port=SOCKS5_IPV4_PORT,
            username=LOGIN,
            password=PASSWORD,
        )
        timeout = httpx.Timeout(2, connect=32)
        with pytest.raises(httpx.ReadTimeout):
            async with httpx.AsyncClient(transport=transport,
                                         timeout=timeout) as client:
                await client.get(HTTP_URL_DELAY_3_SEC)

    curio.run(main)


def test_socks5_proxy_with_connect_timeout():
    async def main():
        transport = AsyncProxyTransport(
            proxy_type=ProxyType.SOCKS5,
            proxy_host=SOCKS5_IPV4_HOST,
            proxy_port=SOCKS5_IPV4_PORT,
            username=LOGIN,
            password=PASSWORD,
        )
        timeout = httpx.Timeout(32, connect=0.001)
        with pytest.raises(ProxyTimeoutError):
            async with httpx.AsyncClient(transport=transport,
                                         timeout=timeout) as client:
                await client.get(HTTP_TEST_URL)

    curio.run(main)


def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port):
    async def main():
        transport = AsyncProxyTransport(
            proxy_type=ProxyType.SOCKS5,
            proxy_host=SOCKS5_IPV4_HOST,
            proxy_port=unused_tcp_port,
            username=LOGIN,
            password=PASSWORD,
        )
        with pytest.raises(ProxyConnectionError):
            async with httpx.AsyncClient(transport=transport) as client:
                await client.get(HTTP_TEST_URL)

    curio.run(main)


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
def test_socks5_proxy_ipv6():
    async def main():
        transport = AsyncProxyTransport.from_url(SOCKS5_IPV6_URL)
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(HTTP_TEST_URL)
            assert resp.status_code == 200

    curio.run(main)


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
def test_socks4_proxy(url, rdns):
    async def main():
        transport = AsyncProxyTransport.from_url(SOCKS4_URL, rdns=rdns, )
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(url)
            assert resp.status_code == 200

    curio.run(main)


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
def test_http_proxy(url):
    async def main():
        transport = AsyncProxyTransport.from_url(HTTP_PROXY_URL)
        async with httpx.AsyncClient(transport=transport) as client:
            resp = await client.get(url)
            assert resp.status_code == 200

    curio.run(main)
