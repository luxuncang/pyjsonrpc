import asyncio
import mimetypes
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aiohttp import AioClient

async def test_async_iter(n: int):
    for i in range(n):
        await asyncio.sleep(1)
        yield i, b"hello world"

namespace = {
    "ping": lambda x: f"pong {x}",
    "test_async_iter": test_async_iter, 
}

rpc = JsonRpc(
    name="client_test_1",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    c_obj = ProxyObj(rpc, "client_test_2")
    s_obj = ProxyObj(rpc)

    print(await c_obj.Test(1, 2).a)

    async for i in s_obj.test_async_iter(10):
        print(i)
    
    async for i in c_obj.test_async_iter(10):
        print(i)
    
    print(await s_obj.ping(c_obj.ping("hello")))
    print(await c_obj.ping(s_obj.ping("hello")))
    print(await c_obj.ping(c_obj.Test(1, 2).a))

    img = c_obj.Image.of(
        data=b"ksk",
        mime=mimetypes.guess_type("kcito.jpg")[0]
    )
    save = c_obj.App.get_save(name="test")
    await save.save(123, [img])

loop = asyncio.get_event_loop()
loop.run_until_complete(main())