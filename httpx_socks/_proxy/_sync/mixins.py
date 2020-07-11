import socket
from ..errors import ProxyError


class StreamSocketReadWriteMixin:
    _socket: socket.socket = None

    def write(self, request):
        data = bytearray()
        for item in request:
            if isinstance(item, int):
                data.append(item)
            elif isinstance(item, (bytearray, bytes)):
                data += item
            else:
                raise ValueError('Unsupported request type')
        self._socket.sendall(data)

    def write_all(self, data):
        self._socket.sendall(data)

    def read(self, n):
        data = bytearray()
        while len(data) < n:
            packet = self._socket.recv(n - len(data))
            if not packet:
                raise ProxyError('Connection closed unexpectedly')
            data += packet
        return data

    def read_all(self, buff_size=4096):
        data = bytearray()
        while True:
            packet = self._socket.recv(buff_size)
            if not packet:
                break
            data += packet
            if len(packet) < buff_size:
                break
        return data


class ResolveMixin:
    # noinspection PyMethodMayBeStatic
    def resolve(self, host, port=0, family=socket.AF_UNSPEC):
        infos = socket.getaddrinfo(
            host=host, port=port,
            family=family, type=socket.SOCK_STREAM)

        if not infos:
            raise OSError('Can`t resolve address {}:{} [{}]'.format(
                host, port, family))

        infos = sorted(infos, key=lambda info: info[0])

        family, _, _, _, address = infos[0]
        return family, address[0]
