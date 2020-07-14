from ._resolver_async import AsyncResolver


class AsyncSocketStream:

    async def open_connection(self, host, port):
        raise NotImplementedError()  # pragma: no cover

    async def close(self):
        raise NotImplementedError()  # pragma: no cover

    async def write(self, request):
        raise NotImplementedError()  # pragma: no cover

    async def write_all(self, data):
        raise NotImplementedError()  # pragma: no cover

    async def read(self, max_bytes):
        raise NotImplementedError()  # pragma: no cover

    async def read_exact(self, n):
        raise NotImplementedError()  # pragma: no cover

    async def read_all(self, buff_size=4096):
        raise NotImplementedError()  # pragma: no cover

    @property
    def resolver(self) -> AsyncResolver:
        raise NotImplementedError()  # pragma: no cover

    @property
    def socket(self):
        raise NotImplementedError()  # pragma: no cover
