import httpcore
import httpx
# noinspection PyPackageRequirements
import pytest

from httpx_socks import (
    ProxyType,
    AsyncProxyTransport,
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
@pytest.mark.trio
async def test_socks5_proxy_ipv4(url, rdns):
    transport = AsyncProxyTransport.from_url(SOCKS5_IPV4_URL, rdns=rdns)
    async with httpx.AsyncClient(transport=transport) as client:
        resp = await client.get(url)
        assert resp.status_code == 200


@pytest.mark.trio
async def test_socks5_proxy_with_invalid_credentials():
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


@pytest.mark.trio
async def test_socks5_proxy_with_read_timeout():
    transport = AsyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=SOCKS5_IPV4_HOST,
        proxy_port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    timeout = httpx.Timeout(2, connect_timeout=32)
    with pytest.raises(httpcore.ReadTimeout):
        async with httpx.AsyncClient(transport=transport,
                                     timeout=timeout) as client:
            await client.get(HTTP_URL_DELAY_3_SEC)


@pytest.mark.trio
async def test_socks5_proxy_with_connect_timeout():
    transport = AsyncProxyTransport(
        proxy_type=ProxyType.SOCKS5,
        proxy_host=SOCKS5_IPV4_HOST,
        proxy_port=SOCKS5_IPV4_PORT,
        username=LOGIN,
        password=PASSWORD,
    )
    timeout = httpx.Timeout(32, connect_timeout=0.001)
    with pytest.raises(ProxyTimeoutError):
        async with httpx.AsyncClient(transport=transport,
                                     timeout=timeout) as client:
            await client.get(HTTP_TEST_URL)


@pytest.mark.trio
async def test_socks5_proxy_with_invalid_proxy_port(unused_tcp_port):
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


@pytest.mark.skipif(SKIP_IPV6_TESTS, reason='TravisCI doesn`t support ipv6')
@pytest.mark.trio
async def test_socks5_proxy_ipv6():
    transport = AsyncProxyTransport.from_url(SOCKS5_IPV6_URL)
    async with httpx.AsyncClient(transport=transport) as client:
        resp = await client.get(HTTP_TEST_URL)
        assert resp.status_code == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.parametrize('rdns', (True, False))
@pytest.mark.trio
async def test_socks4_proxy(url, rdns):
    transport = AsyncProxyTransport.from_url(SOCKS4_URL, rdns=rdns, )
    async with httpx.AsyncClient(transport=transport) as client:
        resp = await client.get(url)
        assert resp.status_code == 200


@pytest.mark.parametrize('url', (HTTP_TEST_URL, HTTPS_TEST_URL))
@pytest.mark.trio
async def test_http_proxy(url):
    transport = AsyncProxyTransport.from_url(HTTP_PROXY_URL)
    async with httpx.AsyncClient(transport=transport) as client:
        resp = await client.get(url)
        assert resp.status_code == 200
