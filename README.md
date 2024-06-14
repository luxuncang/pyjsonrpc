<div align="center">

# Lacia

_A modern `Json-Rpc/Bson-Rpc` implementation, compatible with `Json-Rpc Ast` and `Json-Rpc 2.0` and `Json-Rpc X`, supports multiple network protocols and backend frameworks and supports bidirectional calls._

> 人间总有一两风，填我十万八千梦

 [![CodeFactor](https://www.codefactor.io/repository/github/luxuncang/lacia/badge)](https://www.codefactor.io/repository/github/luxuncang/lacia)
 [![GitHub](https://img.shields.io/github/license/luxuncang/lacia)](https://github.com/luxuncang/lacia/blob/master/LICENSE)
 [![CodeQL](https://github.com/luxuncang/lacia/workflows/CodeQL/badge.svg)](https://github.com/luxuncang/lacia/blob/master/.github/workflows/codeql.yml)

</div>

## 安装

```bash
pip install lacia>=0.2
```

```bash
pdm add lacia>=0.2
```


## 特性

* [X] 跨语言
  * [X] `Python3`
  * [ ] `JavaScript/TypeScript`
  * [ ] `Golang`
  * [ ] `C/C++`
  * [ ] `Java`
  * [ ] `Rust`
* [X] 多种网络协议支持
  * [X] `HTTP`
  * [X] `WebSocket`
  * [X] `自定义`
* [X] 多种Runtime支持
    * [X] 兼容 Json-Rpc Ast 规范
    * [ ] 兼容 Json-Rpc 2.0 规范
    * [ ] 兼容 Json-Rpc X 规范
* [X] 支持完备的链式调用
* [X] 支持嵌套调用 
* [X] 支持双向调用 (StoC, CtoS, CtoC)
* [X] 双向流式传输
* [X] 支持 BSON
* [ ] IDE 支持
* [ ] 分布式Server

## 使用

### 入门

**Server 端**

```python
from lacia.core.core import JsonRpc
from lacia.network.server.aioserver import AioServer, mount_app

namespace = {
    "ping": lambda x: f"pong {x}",
}

rpc = JsonRpc(name = "server_test", namespace=namespace)

if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)
```

**Client 端**

```python
import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

rpc = JsonRpc(
    name="client_test",
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    ping = ProxyObj(rpc).ping

    assert await ping("hello") == "pong hello"

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### 链式调用

**Server 端**

```python
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

rpc = JsonRpc(
    name="client_test",
)

class Test:

    def __init__(self, a, b) -> None:
        self.a = a
        self.b = b
    
    def output(self, name):
        return f"hello: {name}, a: {self.a}, b: {self.b}"

namespace = {
    "Test": Test
}

rpc = JsonRpc(name = "server_test", namespace=namespace)

if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)
```

**Client 端**

```python
import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

rpc = JsonRpc(
    name="client_test",
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    Test = ProxyObj(rpc).Test

    assert await Test(1, 2).output("world") == "hello: world, a: 1, b: 2"

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### 反向调用

**Server 端**

```python

import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.server.aioserver import AioServer, mount_app

namespace = {
    "ping": lambda x: f"pong {x}",
}

rpc = JsonRpc(name = "server_test", namespace=namespace)

async def reverse_call(name: str):
    res = await ProxyObj(rpc, name=name).ping(name)
    return res

rpc.add_namespace({
    "reverse_call": reverse_call,
})

if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)
```

**Client 端**

```python
from pprint import pprint

import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

namespace = {
    "ping": lambda x: f"pong {x}",
}

rpc = JsonRpc(
    name="client_test",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    proxy1 = ProxyObj(rpc).reverse_call
    assert await proxy1("hello") == "pong hello"

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### 流式调用

**Server 端**

```python

import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.server.aioserver import AioServer, mount_app

async def test_async_iter(n: int):
    for i in range(n):
        await asyncio.sleep(1)
        yield i

namespace = {
    "test_async_iter": test_async_iter,
}

rpc = JsonRpc(name = "server_test", namespace=namespace)

if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)
```

**Client 端**

```python
from pprint import pprint

import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

namespace = {
    "ping": lambda x: f"pong {x}",
}

rpc = JsonRpc(
    name="client_test",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    proxy3 = ProxyObj(rpc).test_async_iter

    async for i in proxy3(3):
        print(i)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### 反向流式调用

**Server 端**

```python

import asyncio
from lacia.core.core import JsonRpc, Context
from lacia.core.proxy import ProxyObj
from lacia.network.server.aioserver import AioServer, mount_app

async def test_async_iter(n: int):
    name = Context.name.get()
    obj = ProxyObj(Context.rpc.get(), name)
    async for i in obj.test_async_iter(n):
        yield i

namespace = {
    "test_async_iter": test_async_iter,
}

rpc = JsonRpc(name = "server_test", namespace=namespace)

if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)
```

**Client 端**

```python
import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

async def test_async_iter(n: int):
    for i in range(n):
        await asyncio.sleep(1)
        yield i

namespace = {
    "test_async_iter": test_async_iter,
}

rpc = JsonRpc(
    name="client_test",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    proxy = ProxyObj(rpc).test_async_iter

    async for i in proxy(3):
        print(i)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```


### 嵌套调用

**Server 端**

```python

import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.server.aioserver import AioServer, mount_app

class Test:

    def __init__(self, a, b) -> None:
        self.a = a
        self.b = b
    
    def output(self, name):
        return f"hello: {name}"

def class_sum(obj: Test):
    return obj.a + obj.b

namespace = {
    "class_sum": class_sum,
    "Test": Test,
}

rpc = JsonRpc(name = "server_test", namespace=namespace)

if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)
```

**Client 端**

```python
from pprint import pprint

import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

namespace = {
    "ping": lambda x: f"pong {x}",
}

rpc = JsonRpc(
    name="client_test",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    proxy1 = ProxyObj(rpc).Test(1, b=2)
    proxy2 = ProxyObj(rpc).class_sum(proxy1)

    assert await proxy2 == 3

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### Client to Client

**Server 端**

```python
import asyncio
from lacia.core.core import JsonRpc, Context
from lacia.core.proxy import ProxyObj
from lacia.network.server.aioserver import AioServer

namespace = {
    "ping": lambda x: f"pong {x}",
}

rpc = JsonRpc(name = "server_test")

if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)
```

**Client 端 A**

```python
import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

async def test_async_iter(n: int):
    for i in range(n):
        await asyncio.sleep(1)
        yield i

namespace = {
    "ping": lambda x: f"pong {x}",
    "test_async_iter": test_async_iter,
}

rpc = JsonRpc(
    name="client_test_A",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()
```

**Client 端 B**

```python
import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aioclient import AioClient

namespace = {
    "ping": lambda x: f"pong {x}",
}

rpc = JsonRpc(
    name="client_test_B",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    c_obj = ProxyObj(rpc, "client_test_A")
    s_obj = ProxyObj(rpc)

    async for i in c_obj.test_async_iter(10):
        print(i)
    
    print(await s_obj.ping(c_obj.ping("hello")))
    print(await c_obj.ping(s_obj.ping("hello")))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```
