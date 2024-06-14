import asyncio
from typing import Optional, Dict, TYPE_CHECKING

import orjson
import bson
from starlette.websockets import WebSocket

from lacia.network.abcbase import BaseServer, Connection
from lacia.logger import logger
from lacia.utils.tool import CallObj
from lacia.exception import JsonRpcWsConnectException

if TYPE_CHECKING:
    from lacia.core.core import JsonRpc

    from starlette.applications import Starlette
    from starlette.routing import WebSocketRoute


class StarletteServer(BaseServer[WebSocket]):
    on_events = {}

    def __init__(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self.active_connections: Connection[WebSocket] = Connection()
        self.name_connections: Dict[str, WebSocket] = {}
        self.loop = loop

    async def websocket_handler(self, websocket: WebSocket):
        event = asyncio.Event()
        await websocket.accept()
        self.active_connections.set_ws(websocket, event)

        logger.success(f"{str(websocket)} connected.")

        obj = self.on_events.get("connect")
        if obj is not None and obj.method is not None:
            await obj.method(websocket, *obj.args, **obj.kwargs)

        await event.wait()

    def disconnect(self, websocket: WebSocket):
        for ws, event in self.active_connections.ws.items():
            if ws == websocket:
                event.set()
                self.active_connections.clear_ws(ws)
                break

    async def receive(self, websocket: WebSocket):
        try:
            data = await websocket.receive()
            if data["type"] == "websocket.disconnect":
                raise JsonRpcWsConnectException(str(data["code"]))
            else:
                return data
        except Exception as e:
            await self.close_ws(websocket)
            raise JsonRpcWsConnectException(f"{self.__class__.__name__} closed.")

    async def receive_json(self, websocket: WebSocket):
        data = await self.receive(websocket)
        if data["type"] == "websocket.receive" and "text" in data:
            return orjson.loads(data["text"])
        elif data["type"] == "websocket.receive" and "bytes" in data:
            return bson.loads(data["bytes"])
        raise JsonRpcWsConnectException("Invalid data type.")

    async def receive_bytes(self, websocket: WebSocket):
        data = await self.receive(websocket)
        if data["type"] == "websocket.receive" and "bytes" in data:
            return data["bytes"]

    async def iter_bytes(self, websocket: WebSocket):
        ws_name = str(websocket)
        try:
            while True:
                data = await self.receive_bytes(websocket)
                if data:
                    yield data
        except JsonRpcWsConnectException:
            logger.info(f"{ws_name} disconnected.")
        except Exception as e:
            print(e)
            logger.info(f"{ws_name} disconnected.")
        finally:
            return

    async def iter_json(self, websocket: WebSocket):
        ws_name = str(websocket)
        try:
            while True:
                data = await self.receive_json(websocket)
                if data:
                    yield data
        except JsonRpcWsConnectException:
            logger.info(f"{ws_name} disconnected.")
        except Exception as e:
            print(e)
            logger.info(f"{ws_name} disconnected.")
        finally:
            return

    async def send_json(self, websocket: WebSocket, message: dict, binary: bool = True):
        if binary:
            await websocket.send_bytes(bson.dumps(message))
        else:
            await websocket.send_text(orjson.dumps(message).decode())

    async def send_bytes(self, websocket: WebSocket, message: bytes):
        await websocket.send_bytes(message)

    async def close_ws(self, websocket: WebSocket):
        name = str(websocket)
        obj = self.on_events.get("disconnect")
        if obj is not None and obj.method is not None:
            await obj.method(websocket, *obj.args, **obj.kwargs)
        self.disconnect(websocket)
        await self.on_shutdown()
        logger.info(f"{name} disconnected.")

    async def on_shutdown(self):
        for ws, event in self.active_connections.ws.items():
            await ws.close(code=1001)
            event.set()

    def on(
        self,
        event: str,
        func,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
    ) -> None:
        self.on_events[event] = CallObj(method=func, args=args, kwargs=kwargs)


def mount_app(
    app: "Starlette",
    server: StarletteServer,
    rpc: "JsonRpc",
    path: str = "/ws",
    **kwargs,
):
    async def startup_func():
        await rpc.run_server(server)

    app.add_event_handler("startup", startup_func)
    app.add_websocket_route(path, server.websocket_handler, **kwargs)
