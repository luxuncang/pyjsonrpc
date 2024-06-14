
import builtins

from aiohttp import web

from lacia.core.core import JsonRpc, Context
from lacia.network.server.aiohttp import AioServer, mount_app


async def get_ws():
    ws = Context.websocket.get()
    assert isinstance(ws, web.WebSocketResponse)
    return ws


namespace = {"get_ws": get_ws, "remote_builtins": builtins}

rpc = JsonRpc(name="server_test", namespace=namespace)

rpc = JsonRpc(name="server_test", namespace=namespace)
server = AioServer()


if __name__ == "__main__":

    from aiohttp import web
    app = web.Application()
    mount_app(app=app, server=server, rpc=rpc, path="/ws")
    web.run_app(app, host="localhost", port=8080)