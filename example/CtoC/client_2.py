import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aiohttp import AioClient
from dataclasses import dataclass

class Test:

    def __init__(self, a, b):
        self.a = a
        self.b = b

async def test_async_iter(n: int):
    for i in range(n):
        await asyncio.sleep(1)
        yield i


@dataclass
class Image:
    data: bytes
    mime: str

    @classmethod
    def of(cls, data: bytes, mime: str):
        return cls(data, mime)

class Save:

    async def save(self, uid, image: list[Image]):
        print(uid)
        print(image[0].mime)
        print(image[0].data)

class App:

    def get_save(self, name):
        return Save()

namespace = {
    "ping": lambda x: f"pong {x}",
    "test_async_iter": test_async_iter,
    "Test": Test,
    "App": App(),
    "Image": Image,
}

rpc = JsonRpc(
    name="client_test_2",
    namespace=namespace
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()