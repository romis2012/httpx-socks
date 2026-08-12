from __future__ import annotations

import typing
from multiprocessing import Process

from tests.http_app2 import run_app


class HttpServerConfig(typing.NamedTuple):
    host: str
    port: int
    certfile: str | None = None
    keyfile: str | None = None

    def to_dict(self) -> dict[str, typing.Any]:
        return {key: val for key, val in self._asdict().items() if val is not None}


class HttpServer:
    def __init__(self, config: typing.Iterable[HttpServerConfig]) -> None:
        self.config = config
        self.workers: list[Process] = []

    def start(self) -> None:
        for cfg in self.config:
            p = Process(target=run_app, kwargs=cfg.to_dict())
            self.workers.append(p)

        for p in self.workers:
            p.start()

    def terminate(self) -> None:
        for p in self.workers:
            p.terminate()
