import asyncio
import json
import richuru
from uuid import uuid4
from typing import Dict, Any, Optional, TypeVar, Generic

from nest_asyncio import apply as nest_apply

from lacia.core.abcbase import BaseJsonRpc
from lacia.core.proxy import BaseProxy, ResultProxy, ProxyObj
from lacia.network.abcbase import BaseServer, BaseClient
from lacia.standard.abcbase import BaseDataTrans, Namespace
from lacia.standard.execute import Standard
from lacia.logger import logger
from lacia.types import RpcMessage, Context
from lacia.exception import JsonRpcInitException

T = TypeVar("T")


class JsonRpc(BaseJsonRpc, Generic[T]):
    def __init__(
        self,
        name: str,
        execer: bool = True,
        namespace: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        debug: bool = False,
    ) -> None:
        self._name = name
        self._execer = execer
        self._namespace = Namespace(
            globals=namespace if namespace else {},
        )
        self._token = token
        self._loop = loop
        self._debug = debug
        self._uuid = str(uuid4())

        self._wait_remote: Dict[str, asyncio.Event] = {}
        self._wait_result: Dict[str, ResultProxy] = {}

        self._standard = Standard()

        if self._debug:
            richuru.install(level="DEBUG")

    def add_namespace(self, namespace: Dict[str, Any]) -> None:
        self._namespace.globals.update(namespace)

    async def run_client(self, client: BaseClient) -> None:
        self._standard.init_standard()
        self._client = client
        self._loop = self._loop or asyncio.get_event_loop()
        await client.start()
        if self._loop:
            self._loop.create_task(self._listening_server(self._client.ws))
            logger.info("run client")

    async def run_server(self, server: BaseServer) -> None:
        self._loop = self._loop or asyncio.get_event_loop()
        # nest_apply()
        self._standard.init_standard()
        self._server = server
        self._server.on("connect", self._listening_client)
        self._server.on("disconnect", self.on_server_close)
        logger.info("run server")

    async def _listening_client(self, websocket: T):
        logger.info("listening client")
        Context.websocket.set(websocket)
        Context.namespace.set(self._namespace)
        Context.rpc.set(self)
        by_name: Optional[str] = None

        event = asyncio.Event()

        def rpc_auto_register(name, token):
            nonlocal by_name
            if self._server is not None:
                self._server.active_connections.set_name_ws(name, websocket)
            Context.name.set(name)
            by_name = name
            if token == self._token:
                event.set()
                return self._name
            raise JsonRpcInitException("rpc_auto_register fail")

        if self._namespace.locals.get(websocket) is None:
            self._namespace.locals[websocket] = {}
        if self._server:
            self._namespace.locals[websocket]["rpc_auto_register"] = rpc_auto_register

        qmgs = asyncio.Queue()

        if self._loop:
            self._loop.create_task(self._client_auth(event, qmgs, websocket))

        if self._server is not None:
            async for message in self._server.iter_json(websocket):
                logger.debug(f"receive: {message}")
                msg = RpcMessage(message)
                if msg.is_request and self._execer and self._loop:
                    if msg.is_auth:
                        self._loop.create_task(self._s_execute(websocket, msg))
                    else:
                        qmgs.put_nowait(msg)
                elif msg.is_response:
                    rmsg = ResultProxy(msg, core=self, by=by_name)  # type: ignore
                    self._wait_result[msg.id] = rmsg
                    self._wait_remote[msg.id].set()
        else:
            raise JsonRpcInitException("server is None")

    async def _listening_server(self, websocket: T):
        logger.info("listening server")
        Context.websocket.set(websocket)
        Context.namespace.set(self._namespace)
        Context.rpc.set(self)
        Context.name.set(None)  # type: ignore

        if self._client is not None:
            if self._loop:
                self._loop.create_task(
                    self.run(ProxyObj().rpc_auto_register(self._name, self._token))
                )

            async for message in self._client.iter_json():
                logger.debug(f"receive: {message}")
                msg = RpcMessage(message)

                if msg.is_request and self._execer and self._loop:
                    self._loop.create_task(self._c_execute(websocket, msg))
                elif msg.is_response:
                    rmsg = ResultProxy(msg, core=self, by=None)  # type: ignore
                    self._wait_result[msg.id] = rmsg
                    self._wait_remote[msg.id].set()
        else:
            raise JsonRpcInitException("client is None")

    async def _s_execute(self, websocket: T, message: RpcMessage):
        result, error = await self._standard.rpc_request(
            message.data, self._namespace[websocket], ProxyObj, ResultProxy
        )

        if error is None:
            if websocket not in self._namespace.locals:
                self._namespace.locals[websocket] = {}
            self._namespace.locals[websocket][message.id] = result
            msg = {
                "jsonrpc": message.jsonrpc,
                "id": message.id,
                "result": self._pretreatment(result),
            }
        else:
            msg = {"jsonrpc": message.jsonrpc, "id": message.id, "error": error}
        if self._server is not None:
            logger.debug(f"send: {msg}")

            await self._server.send_json(websocket, msg)

    async def _c_execute(self, websocket: T, message: RpcMessage):
        result, error = await self._standard.rpc_request(
            message.data, self._namespace[websocket], ProxyObj, ResultProxy
        )

        if error is None:
            if websocket not in self._namespace.locals:
                self._namespace.locals[websocket] = {}
            self._namespace.locals[websocket][message.id] = result  # TODO 内存泄漏
            msg = {
                "jsonrpc": message.jsonrpc,
                "id": message.id,
                "result": self._pretreatment(result),
            }
        else:
            msg = {"jsonrpc": message.jsonrpc, "id": message.id, "error": error}

        if self._client is not None:
            logger.debug(f"send: {msg}")
            await self._client.send_json(msg)

    def on_client_close(self, websocket: T):
        del self._namespace.locals[websocket]

    def on_server_close(self, websocket: T):
        del self._namespace.locals[websocket]

    async def run(self, proxy: BaseProxy[BaseDataTrans]):
        uuid_str = str(uuid4())
        if proxy._obj is None:
            raise JsonRpcInitException("proxy._obj is None")
        data = proxy._obj.dumps()
        event = asyncio.Event()

        self._wait_remote[uuid_str] = event

        msg = {
            "jsonrpc": proxy._jsonrpc,
            "id": uuid_str,
            "method": data,
        }

        if self._client is not None:
            logger.debug(f"send: {msg}")
            await self._client.send_json(msg)
        else:
            raise JsonRpcInitException("server and client are None R")

        await event.wait()

        return self._wait_result.pop(uuid_str)

    async def reverse_run(self, name: str, proxy: BaseProxy[BaseDataTrans]):
        uuid_str = str(uuid4())
        if proxy._obj is None:
            raise JsonRpcInitException("proxy._obj is None")
        data = proxy._obj.dumps()
        event = asyncio.Event()

        self._wait_remote[uuid_str] = event

        msg = {
            "jsonrpc": proxy._jsonrpc,
            "id": uuid_str,
            "method": data,
        }

        if self._server is not None:
            logger.debug(f"send: {msg}")
            await self._server.send_json(
                self._server.active_connections.get_ws(name), msg
            )
        else:
            raise JsonRpcInitException("server and client are None S")

        await event.wait()

        return self._wait_result.pop(uuid_str)

    async def _client_auth(
        self, event: asyncio.Event, qmgs: asyncio.Queue, websocket: T
    ):
        await event.wait()
        if self._server is not None:
            Context.name.set(self._server.active_connections.get_name(websocket))
        while True:
            msg = await qmgs.get()
            await self._s_execute(websocket, msg)

    def _pretreatment(self, data: Any) -> Any:
        class BytesEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, bytes):
                    return None
                return super().default(obj)

        try:
            json.dumps(data, cls=BytesEncoder)
            return data
        except TypeError:
            return str(data)

    def is_server(self) -> bool:
        if self._server is None and self._client is None:
            raise JsonRpcInitException("server and client are None")
        elif self._client is None and self._server is not None:
            return True
        return False

    @property
    def jsonast(self):
        return ProxyObj(self)  # type: ignore
