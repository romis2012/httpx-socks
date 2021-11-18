import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route


async def ip(request: Request):
    return PlainTextResponse(content=request.client.host)


async def delay(request: Request):
    seconds = request.path_params['seconds']
    await asyncio.sleep(seconds)
    return PlainTextResponse(content='ok')


app = Starlette(
    debug=True,
    routes=[
        Route('/ip', ip),
        Route('/delay/{seconds:int}', delay),
    ],
)


def run_app(host: str, port: int, certfile: str = None, keyfile: str = None):
    config = Config()
    config.bind = ['{}:{}'.format(host, port)]
    config.certfile = certfile
    config.keyfile = keyfile
    asyncio.run(serve(app, config))  # type: ignore
