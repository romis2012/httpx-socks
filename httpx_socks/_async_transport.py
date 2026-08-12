from __future__ import annotations

import ssl
from collections.abc import AsyncIterable
from types import TracebackType
from typing import Any

import httpcore
from httpx import AsyncBaseTransport, AsyncByteStream, Limits, Request, Response
from httpx._config import DEFAULT_LIMITS, create_ssl_context
from httpx._transports.default import AsyncResponseStream, map_httpcore_exceptions
from httpx._types import CertTypes
from python_socks import ProxyType, parse_proxy_url

from ._async_proxy import AsyncProxy


class AsyncProxyTransport(AsyncBaseTransport):
    def __init__(  # noqa: PLR0913
        self,
        *,
        proxy_type: ProxyType,
        proxy_host: str,
        proxy_port: int,
        username: str | None = None,
        password: str | None = None,
        rdns: bool | None = None,
        proxy_ssl: ssl.SSLContext | None = None,
        verify: ssl.SSLContext | str | bool | None = True,
        cert: CertTypes | None = None,
        trust_env: bool = True,
        limits: Limits = DEFAULT_LIMITS,
        **kwargs: Any,
    ) -> None:
        if verify is None:
            verify = False

        ssl_context = create_ssl_context(
            verify=verify,
            cert=cert,
            trust_env=trust_env,
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

        assert isinstance(resp.stream, AsyncIterable)

        return Response(
            status_code=resp.status,
            headers=resp.headers,
            stream=AsyncResponseStream(resp.stream),
            extensions=resp.extensions,
        )

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> AsyncProxyTransport:
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

    async def __aenter__(self) -> AsyncProxyTransport:  # noqa: PYI034
        await self._pool.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        with map_httpcore_exceptions():
            await self._pool.__aexit__(exc_type, exc_value, traceback)
