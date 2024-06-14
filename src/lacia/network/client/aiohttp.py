import asyncio 
from typing import Optional

import orjson
import bson
import aiohttp

from lacia.network.abcbase import BaseClient
from lacia.logger import logger
from lacia.types import Message
from lacia.exception import JsonRpcWsConnectException



class AioClient(BaseClient):
    def __init__(
        self,
        path: str = "",
        host: str = "localhost",
        port: int = 8080,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        self.path = path
        self.host = host
        self.port = port
        self.loop = loop

    async def start(self) -> "AioClient":
        self.session = aiohttp.ClientSession(loop=self.loop or asyncio.get_event_loop())
        self.ws = await self.session.ws_connect(f"http://{self.host}:{self.port}{self.path}")
        logger.success(f"📡 {self.__class__.__name__} success connected: http://{self.host}:{self.port}{self.path}.")
        return self

    async def receive(self):

        try:
            async for data in self.ws:
                if data.type == aiohttp.WSMsgType.close:
                    raise JsonRpcWsConnectException(data.data)
                else:
                    return data
        except Exception as e:
            raise JsonRpcWsConnectException(f"{self.__class__.__name__} closed.({e})")

    async def receive_json(self):
        data = await self.receive()
        if data and data.type == aiohttp.WSMsgType.TEXT:
            data = orjson.loads(data.data)
            return data
        elif data and data.type == aiohttp.WSMsgType.BINARY:
            data = bson.loads(data.data)
            return data
        raise JsonRpcWsConnectException("Invalid data type.")

    async def receive_bytes(self):
        data = await self.receive()
        if data and data.type == aiohttp.WSMsgType.BINARY:
            return data.data

    async def iter_json(self) :
        try:
            while True:
                data = await self.receive_json()
                if data:
                    yield data
        except JsonRpcWsConnectException as e:
            logger.error(f"http://{self.host}:{self.port}{self.path} closed.")
            await self.close()
        except Exception as e:
            logger.error(e)
            logger.error(f"http://{self.host}:{self.port}{self.path} closed.")
            await self.close()
        finally:
            return

    async def iter_bytes(self):
        try:
            while True:
                data = await self.receive_bytes()
                if data:
                    yield data
        except JsonRpcWsConnectException as e:
            logger.info(f"http://{self.host}:{self.port}{self.path} closed.")
            await self.close()
        except Exception as e:
            logger.error(e)
            logger.info(f"http://{self.host}:{self.port}{self.path} closed.")
            await self.close()

    async def send(self, message) -> None:
        return await self.send(message)

    async def send_bytes(self, message: bytes):
        return await self.ws.send_bytes(message)

    async def send_json(self, message: Message, binary: bool = True):
        if binary:
            return await self.ws.send_bytes(bson.dumps(message))
        return await self.ws.send_json(message)

    async def close(self) -> None:
        await self.ws.close()

    def closed(self) -> bool:
        return self.ws.closed
