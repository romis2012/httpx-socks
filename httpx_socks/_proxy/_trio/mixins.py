import trio.socket
from ..errors import ProxyError


class StreamSocketReadWriteMixin:
    _socket = None

    async def write(self, request):
        data = bytearray()
        for item in request:
            if isinstance(item, int):
                data.append(item)
            elif isinstance(item, (bytearray, bytes)):
                data += item
            else:
                raise ValueError('Unsupported request type')
        # await self._socket.send(data)
        await self.write_all(data)

    async def write_all(self, data):
        total_sent = 0
        while total_sent < len(data):
            remaining = data[total_sent:]
            sent = await self._socket.send(remaining)
            total_sent += sent

    async def read(self, n):
        data = bytearray()
        while len(data) < n:
            packet = await self._socket.recv(n - len(data))
            if not packet:
                raise ProxyError('Connection closed unexpectedly')
            data += packet
        return data

    async def read_all(self, buff_size=4096):
        data = bytearray()
        while True:
            packet = await self._socket.recv(buff_size)
            if not packet:
                break
            data += packet
            if len(packet) < buff_size:
                break
        return data


class ResolveMixin:
    _loop = None

    # noinspection PyMethodMayBeStatic
    async def resolve(self, host, port=0, family=trio.socket.AF_UNSPEC):
        infos = await trio.socket.getaddrinfo(
            host=host, port=port,
            family=family, type=trio.socket.SOCK_STREAM
        )

        if not infos:
            raise OSError('Can`t resolve address {}:{} [{}]'.format(
                host, port, family))

        infos = sorted(infos, key=lambda info: info[0])

        family, _, _, _, address = infos[0]
        return family, address[0]
