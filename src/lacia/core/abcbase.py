from abc import ABC, abstractmethod

from typing import Optional

from lacia.network.abcbase import BaseServer, BaseClient
from lacia.standard.abcbase import Namespace

class BaseJsonRpc(ABC):
    
    _server: Optional[BaseServer] = None
    _client: Optional[BaseClient] = None
    _Executor: bool = False
    _namespace: Namespace

    @abstractmethod
    def run_server(self, server: BaseServer) -> None:
        ...
    
    @abstractmethod
    def run_client(self, client: BaseClient) -> None:
        ...
    
    @abstractmethod
    def is_server(self) -> bool:
        ...
