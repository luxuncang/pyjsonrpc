import asyncio
from abc import abstractmethod
from typing import Optional, TypeVar, Generic, Generator, Dict, Callable

from lacia.types import Message
from lacia.utils.tool import CallObj

T = TypeVar("T")


class Connection(Generic[T]):
    def __init__(self):
        self.ws: Dict[T, asyncio.Event] = {}
        self.name_ws: Dict[str, T] = {}

    def set_ws(self, ws: T, event: asyncio.Event):
        self.ws[ws] = event

    def set_name_ws(self, name: str, ws: T):
        self.name_ws[name] = ws

    def clear_ws(self, ws: T):
        self.ws.pop(ws)
        for name, _ws in self.name_ws.items():
            if _ws == ws:
                self.name_ws.pop(name)

    def clear_name_ws(self, name: str):
        self.name_ws.pop(name)

    def get_ws(self, name: str) -> T:
        return self.name_ws[name]

    def get_name(self, ws: T) -> str:
        for name, _ws in self.name_ws.items():
            if _ws == ws:
                return name
        raise KeyError("no such websocket")


class BaseServer(Generic[T]):
    active_connections: Connection[T]
    name_connections: Dict[str, T]
    on_events: Dict[str, CallObj]

    @abstractmethod
    async def receive(self, websocket: T) -> Message:
        ...

    async def send(self, message) -> None:
        ...

    @abstractmethod
    async def receive_json(self, websocket: T) -> Message:
        ...

    @abstractmethod
    async def receive_bytes(self, websocket: T) -> bytes:
        ...

    @abstractmethod
    async def iter_bytes(self, websocket: T) -> Generator[bytes, None, None]:
        ...

    @abstractmethod
    async def iter_json(self, websocket: T) -> Generator[Message, None, None]:
        ...

    @abstractmethod
    async def send_bytes(self, websocket: T, message: bytes) -> None:
        ...

    @abstractmethod
    async def send_json(self, websocket: T, message: Message, binary=True) -> None:
        ...

    @abstractmethod
    async def start(self) -> "BaseServer":
        ...

    @abstractmethod
    def on(
        self,
        event: str,
        func: Callable,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
    ) -> None:
        ...


class BaseClient(Generic[T]):
    ws: T

    @abstractmethod
    async def receive(self) -> Message:
        ...

    @abstractmethod
    async def send(self, message) -> None:
        ...

    @abstractmethod
    async def receive_json(self) -> Message:
        ...

    @abstractmethod
    async def receive_bytes(self) -> bytes:
        ...

    @abstractmethod
    async def iter_bytes(self) -> Generator[bytes, None, None]:
        ...

    @abstractmethod
    async def iter_json(self) -> Generator[Message, None, None]:
        ...

    @abstractmethod
    async def send_bytes(self, message: bytes) -> None:
        ...

    @abstractmethod
    async def send_json(self, message: Message, binary=True) -> None:
        ...

    @abstractmethod
    async def start(self, *args, **kwargs) -> "BaseClient":
        ...

    @abstractmethod
    async def close(self, code: int, reason: Optional[str] = None) -> None:
        ...

    @abstractmethod
    def closed(self) -> bool:
        ...
