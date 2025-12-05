# httpx-socks

[![CI](https://github.com/romis2012/httpx-socks/actions/workflows/ci.yml/badge.svg)](https://github.com/romis2012/httpx-socks/actions/workflows/ci.yml)
[![Coverage Status](https://codecov.io/gh/romis2012/httpx-socks/branch/master/graph/badge.svg)](https://codecov.io/gh/romis2012/httpx-socks)
[![PyPI version](https://badge.fury.io/py/httpx-socks.svg)](https://pypi.python.org/pypi/httpx-socks)
[![versions](https://img.shields.io/pypi/pyversions/httpx-socks.svg)](https://github.com/romis2012/httpx-socks)
<!--
[![Downloads](https://pepy.tech/badge/httpx-socks/month)](https://pepy.tech/project/httpx-socks)
-->

The `httpx-socks` package provides proxy transports for [httpx](https://github.com/encode/httpx) client. 
SOCKS4(a), SOCKS5(h), HTTP CONNECT proxy supported.
It uses [python-socks](https://github.com/romis2012/python-socks) for core proxy functionality.


## Requirements
- Python >= 3.8
- httpx>=0.28.0,<0.29.0
- python-socks>=2.4.3,<3.0.0
- trio>=0.24 (optional)
- anyio>=3.3.4,<5.0.0 (optional)


## Installation

only sync proxy support:
```
pip install httpx-socks
```

to include optional asyncio support (it requires async-timeout):
```
pip install httpx-socks[asyncio]
```

to include optional trio support:
```
pip install httpx-socks[trio]
```

## Usage

#### sync transport
```python
import httpx
from httpx_socks import SyncProxyTransport

def fetch(url):
    transport = SyncProxyTransport.from_url('socks5://user:password@127.0.0.1:1080')
    with httpx.Client(transport=transport) as client:
        res = client.get(url)
        return res.text
```

#### async transport (asyncio, trio)
```python
import httpx
from httpx_socks import AsyncProxyTransport

async def fetch(url):
    transport = AsyncProxyTransport.from_url('socks5://user:password@127.0.0.1:1080')
    async with httpx.AsyncClient(transport=transport) as client:
        res = await client.get(url)
        return res.text
```

#### secure proxy connections (aka "HTTPS proxies", experimental feature, both sync and async support)
```python
import ssl
import httpx
from httpx_socks import AsyncProxyTransport

async def fetch(url):
    proxy_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS)
    proxy_ssl.verify_mode = ssl.CERT_REQUIRED
    proxy_ssl.load_verify_locations(...)
    
    transport = AsyncProxyTransport.from_url('http://user:password@127.0.0.1:8080', proxy_ssl=proxy_ssl)
    async with httpx.AsyncClient(transport=transport) as client:
        res = await client.get(url)
        return res.text
```
