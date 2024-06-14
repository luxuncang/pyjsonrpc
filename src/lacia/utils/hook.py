import inspect
import asyncio

from functools import wraps

from lacia.logger import logger

from typing import (
    Callable,
    TypeVar,
    Dict,
    Any,
    Optional,
    ParamSpec
)


P = ParamSpec("P")
T = TypeVar("T")

class BaseClass:
    __on_obj: Dict[str, Callable] = {}

    @classmethod
    def on(cls, name: str, func: Optional[Callable] = None):
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return await func(*args, **kwargs)  # type: ignore

            cls.__on_obj[name] = async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore

            return cls.__on_obj[name]  # type: ignore
        if func:
            return decorator(func)
        return decorator

    @classmethod
    def __run(
        cls,
        obj: Any,
        objer: Callable[P, T],
        name: str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        if func := cls.__on_obj.get(name, None):
            return func(obj, objer, name, *args, **kwargs)
        return objer(*args, **kwargs)

    @classmethod
    async def __async_run(
        cls,
        obj: Any,
        objer: Callable[P, T],
        name: str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        if func := cls.__on_obj.get(name, None):
            return await func(obj, objer, name, *args, **kwargs)
        return await objer(*args, **kwargs)  # type: ignore

    @staticmethod
    def __get_func_bind(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Get the function binding.
        """
        sig = inspect.signature(func)
        return {k: v for k, v in sig.bind(*args, **kwargs).arguments.items()}

    @classmethod
    def __hook_func(cls, name: str, obj):
        """
        Hook function for the tool.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return cls.__run(obj, func, name, *args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return await cls.__async_run(obj, func, name, *args, **kwargs)

            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore

        return decorator

    def __getattribute__(self, __name: str):
        if __name.startswith('_'):
            return super().__getattribute__(__name)
        obj = super().__getattribute__(__name)
        if __name in self.__on_obj:
            if callable(obj):
                return self.__hook_func(__name, obj)(obj)
            return self.__run(self, obj, __name)
        return obj


class MetaHook(BaseClass, type):
    ...


class Hook(metaclass = MetaHook):
    __on_obj: Dict[str, Callable] = {}

    @classmethod
    def on(cls, name: str, func: Optional[Callable] = None):
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return await func(*args, **kwargs)  # type: ignore

            cls.__on_obj[name] = async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore

            return cls.__on_obj[name]  # type: ignore
        if func:
            return decorator(func)
        return decorator

    @classmethod
    def __run(
        cls,
        obj: Any,
        objer: Callable[P, T],
        name: str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        if func := cls.__on_obj.get(name, None):
            return func(obj, objer, name, *args, **kwargs)
        return objer(*args, **kwargs)

    @classmethod
    async def __async_run(
        cls,
        obj: Any,
        objer: Callable[P, T],
        name: str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        if func := cls.__on_obj.get(name, None):
            return await func(obj, objer, name, *args, **kwargs)
        return await objer(*args, **kwargs)  # type: ignore

    @staticmethod
    def __get_func_bind(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Get the function binding.
        """
        sig = inspect.signature(func)
        return {k: v for k, v in sig.bind(*args, **kwargs).arguments.items()}

    @classmethod
    def __hook_func(cls, name: str, obj):
        """
        Hook function for the tool.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return cls.__run(obj, func, name, *args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return await cls.__async_run(obj, func, name, *args, **kwargs)

            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper  # type: ignore

        return decorator

    def __getattribute__(self, __name: str):
        if __name.startswith('_'):
            return super().__getattribute__(__name)
        obj = super().__getattribute__(__name)
        if __name in self.__on_obj:
            if callable(obj):
                return self.__hook_func(__name, obj)(obj)
            return self.__run(self, obj, __name)
        return obj


async def receive_json_hook(obj, objer, name, *args, **kwargs):
    res = await objer(*args, **kwargs)
    logger.info(f"{obj.__self__.__class__.__name__} received: {res}")
    return res

async def send_json_hook(obj, objer, name, *args, **kwargs):
    res = await objer(*args, **kwargs)
    logger.info(f"{obj.__self__.__class__.__name__} send: {args[-1] if args else None}")
    return res

# Hook.on('receive_json', receive_json_hook)
# Hook.on('send_json', send_json_hook) 