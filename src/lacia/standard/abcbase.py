from typing import TypeVar, Generic, Type, Any, Dict, NamedTuple, Hashable, Protocol
from typing_extensions import Self

T = TypeVar("T")
S = TypeVar("S", contravariant=True)

class Namespace(NamedTuple):

    builtins: Dict[str, Any] = {}
    globals: Dict[str, Any] = {}
    locals: Dict[Hashable, Dict[str, Any]] = {}

    def __getitem__(self, key: T) -> Dict[str, Any]:

        return {
            **self.builtins,
            **self.globals,
            **self.locals.get(key, {})
        }      

class BaseDataTrans(Protocol[T]):

    @classmethod
    def loads(cls, obj: T) -> Self:
        ...
    
    def dumps(self) -> T:
        ...

class BaseRunTime(Generic[S]):

    def __init__(self, namespace: Dict[str, Any], proxy, proxyresult):
        self.namespace = namespace
        self.proxy = proxy
        self.proxyresult = proxyresult

    async def run(self, obj: S) -> Any:
        ...

class BaseStandard(Protocol[T, S]):
    
    datatrans: Type[BaseDataTrans[T]]
    runtime: Type[BaseRunTime[S]]
