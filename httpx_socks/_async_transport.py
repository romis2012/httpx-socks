import ssl
import typing

import httpcore
from httpx import AsyncBaseTransport, Request, Response, AsyncByteStream, Limits

# noinspection PyProtectedMember
from httpx._config import DEFAULT_LIMITS, create_ssl_context
# noinspection PyProtectedMember
from httpx._transports.default import AsyncResponseStream, map_httpcore_exceptions
from python_socks import ProxyType, parse_proxy_url

from ._async_proxy import AsyncProxy


class AsyncProxyTransport(AsyncBaseTransport):
    def __init__(
        self,
        *,
        proxy_type: ProxyType,
        proxy_host: str,
        proxy_port: int,
        username=None,
        password=None,
        rdns=None,
        proxy_ssl: ssl.SSLContext = None,
        verify=True,
        cert=None,
        trust_env: bool = True,
        limits: Limits = DEFAULT_LIMITS,
        **kwargs,
    ):
        ssl_context = create_ssl_context(
            verify=verify,
            cert=cert,
            trust_env=trust_env,
            http2=kwargs.get('http2', False),
        )

        self._pool = AsyncProxy(
            proxy_type=proxy_type,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            username=username,
            password=password,
            rdns=rdns,
            proxy_ssl=proxy_ssl,
            ssl_context=ssl_context,
            max_connections=limits.max_connections,
            max_keepalive_connections=limits.max_keepalive_connections,
            keepalive_expiry=limits.keepalive_expiry,
            **kwargs,
        )

    async def handle_async_request(self, request: Request) -> Response:
        assert isinstance(request.stream, AsyncByteStream)

        req = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )

        with map_httpcore_exceptions():
            resp = await self._pool.handle_async_request(req)

        assert isinstance(resp.stream, typing.AsyncIterable)

        return Response(
            status_code=resp.status,
            headers=resp.headers,
            stream=AsyncResponseStream(resp.stream),
            extensions=resp.extensions,
        )

    @classmethod
    def from_url(cls, url, **kwargs):
        proxy_type, host, port, username, password = parse_proxy_url(url)
        return cls(
            proxy_type=proxy_type,
            proxy_host=host,
            proxy_port=port,
            username=username,
            password=password,
            **kwargs,
        )

    async def aclose(self) -> None:
        await self._pool.aclose()  # pragma: no cover

    async def __aenter__(self):
        await self._pool.__aenter__()
        return self

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        with map_httpcore_exceptions():
            await self._pool.__aexit__(exc_type, exc_value, traceback)
