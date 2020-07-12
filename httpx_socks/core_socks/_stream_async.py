from ._resolver_async import AsyncResolver


class AsyncSocketStream:

    async def open_connection(self, host, port):
        raise NotImplementedError()

    async def close(self):
        raise NotImplementedError()

    async def write(self, request):
        raise NotImplementedError()

    async def write_all(self, data):
        raise NotImplementedError()

    async def read(self, max_bytes):
        raise NotImplementedError()

    async def read_exact(self, n):
        raise NotImplementedError()

    async def read_all(self, buff_size=4096):
        raise NotImplementedError()

    @property
    def resolver(self) -> AsyncResolver:
        raise NotImplementedError()

    @property
    def socket(self):
        raise NotImplementedError()
