# httpx-socks

Proxy transports for [httpx](https://github.com/encode/httpx) library. 
SOCKS4(a), SOCKS5, HTTP (tunneling) proxy supported.


## Requirements
- Python >= 3.6
- httpx >= 0.13.3
- async-timeout>=3.0.1

## Installation
```
will be available soon, work is still in progress
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

#### async transport (only asyncio backend supported)
```python
import httpx
from httpx_socks import AsyncProxyTransport

async def fetch(url):
    transport = AsyncProxyTransport.from_url('socks5://user:password@127.0.0.1:1080')
    async with httpx.AsyncClient(transport=transport) as client:
        res = await client.get(url)
        return res.text
```
