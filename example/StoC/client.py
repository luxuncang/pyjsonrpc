import asyncio
from lacia.core.core import JsonRpc
from lacia.core.proxy import ProxyObj
from lacia.network.client.aiohttp import AioClient

rpc = JsonRpc(
    name="client_test",
)

async def main():

    client = AioClient(path="/ws")
    await rpc.run_client(client)

    get_ws = ProxyObj(rpc).get_ws
    builtins = ProxyObj(rpc).remote_builtins

    headers = get_ws().headers

    dict_headers = await builtins.dict(headers)

    assert isinstance(dict_headers, dict)

    print(dict_headers)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())