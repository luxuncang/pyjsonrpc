import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aiohttp import AioClient

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

    test = await rpc.run(proxy1)

    assert await test.output("lacia") == "hello: lacia"

    async for i in ProxyObj(rpc).test_async_iter(3):
        print(i)

    proxy3 = ProxyObj(rpc).test_async_iter

    async for i in proxy3(3):
        print(i)

    proxy4 = ProxyObj(rpc).reverse_call("client_test")
    print(await proxy4)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())