# httpx-socks

[![Build Status](https://travis-ci.org/romis2012/httpx-socks.svg?branch=master)](https://travis-ci.org/romis2012/httpx-socks)
[![Coverage Status](https://coveralls.io/repos/github/romis2012/httpx-socks/badge.svg?branch=master&_=x)](https://coveralls.io/github/romis2012/httpx-socks?branch=master)
[![PyPI version](https://badge.fury.io/py/httpx-socks.svg)](https://badge.fury.io/py/httpx-socks)

The `httpx-socks` package provides proxy transports for [httpx](https://github.com/encode/httpx) client. 
SOCKS4(a), SOCKS5, HTTP (tunneling) proxy supported.
It uses [python-socks](https://github.com/romis2012/python-socks) for core proxy functionality.


## Requirements
- Python >= 3.6
- httpx >= 0.13.3
- python-socks[asyncio,trio,curio] >= 1.1.0

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

to include optional curio support:
```
pip install httpx-socks[curio]
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

#### async transport (asyncio, trio, curio)
```python
import httpx
from httpx_socks import AsyncProxyTransport

async def fetch(url):
    transport = AsyncProxyTransport.from_url('socks5://user:password@127.0.0.1:1080')
    async with httpx.AsyncClient(transport=transport) as client:
        res = await client.get(url)
        return res.text
```
