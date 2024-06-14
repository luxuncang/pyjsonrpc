
from typing import TypeVar, Generic, Dict, ClassVar

from lacia.logger import logger
from lacia.types import JsonRpcCode
from lacia.standard.abcbase import BaseStandard, Namespace, BaseRunTime

S = TypeVar("S")

class Standard(Generic[S]):

    execute: Dict[str, BaseStandard[dict, S]] = {}
    
    @classmethod
    def init_standard(cls):
        for name, obj in cls.get_rpc_subclasses(BaseStandard):
            cls.execute[name] = obj
        
    @classmethod
    def get_all_subclasses(cls, obj):

        for subclass in obj.__subclasses__():
            yield from cls.get_all_subclasses(subclass)
            yield subclass
    
    @classmethod
    def get_rpc_subclasses(cls, obj):

        for subclass in cls.get_all_subclasses(obj):
            if hasattr(subclass, "_jsonrpc"):
                yield getattr(subclass, "_jsonrpc"), subclass 

    @classmethod
    async def rpc_request(cls, data: dict, namespace: dict, proxy, proxyresult):
        jsonrpc = data.get("jsonrpc")
        result, error = None, None
        if jsonrpc is None:
            return None, {"code": JsonRpcCode.ParseError, "message": "jsonrpc is None"}
        elif jsonrpc in cls.execute:
            runtime: BaseRunTime = cls.execute[jsonrpc].runtime(namespace, proxy, proxyresult)
            obj = cls.execute[jsonrpc].datatrans.loads(data["method"]) # type: ignore
            try:
                result = await runtime.run(obj)
                if isinstance(result, proxy):
                    result = await result
                if isinstance(result, proxyresult):
                    if data["method"]["method"] not in ("__aiter__", "__anext__"):
                        result = result.visions
            except StopAsyncIteration as e:
                return result, {"code": JsonRpcCode.StopAsyncIterationError, "message": ""}
            except Exception as e:
                error = e
                logger.error(e)
            return result, {"code": JsonRpcCode.InternalError, "message": str(error)} if error else None
        return None, {"code": JsonRpcCode.MethodNotFound, "message": f"jsonrpc {jsonrpc} not found"}

