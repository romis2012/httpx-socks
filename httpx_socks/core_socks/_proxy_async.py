class AsyncProxy:
    async def connect(self, dest_host, dest_port,
                      timeout=None, _socket=None):
        raise NotImplementedError()

    @property
    def proxy_host(self):
        raise NotImplementedError()

    @property
    def proxy_port(self):
        raise NotImplementedError()
