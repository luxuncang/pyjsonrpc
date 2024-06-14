import asyncio
from typing import Dict, Any, Type, TYPE_CHECKING

from lacia.standard.abcbase import BaseRunTime, BaseStandard, Namespace
from lacia.standard.jsonast.impl import JsonAst
from lacia.types import Context

if TYPE_CHECKING:
    from lacia.core.proxy import ProxyObj, ResultProxy


class RunTime(BaseRunTime[JsonAst]):
    def __init__(
        self,
        namespace: Dict[str, Any],
        proxy: Type["ProxyObj"],
        proxyresult: Type["ResultProxy"],
    ):
        self.namespace = namespace
        self.proxy = proxy
        self.proxyresult = proxyresult
        try:
            self.rpc = Context.rpc.get()
            self.is_server = self.rpc.is_server()
            self.self_name = self.rpc._name
        except Exception:
            self.rpc = None
            self.is_server = True
            self.self_name = None

    async def run(self, ast):
        if isinstance(ast, JsonAst):
            if isinstance(ast.obj, JsonAst):
                obj = await self.run(ast.obj)
            elif (
                ast.obj is None
                or (ast.obj == ["server", None] and self.is_server)
                or (ast.obj == ["client", self.self_name] and not self.is_server)
            ):
                if ast.args is not None:
                    if len(ast.args) == 1 and isinstance(ast.args[0], str):
                        obj = self.namespace[ast.args[0]]
                        return obj
                    else:
                        raise TypeError(f"obj type error: {ast.obj}")
                else:
                    raise TypeError(f"obj type error: {ast.obj}")
            elif isinstance(ast.obj, str):
                obj = self.namespace[ast.obj]
            elif (
                isinstance(ast.obj, list)
                and len(ast.obj) == 2
                and ast.obj[0] == "server"
            ):
                obj = self.proxy(self.rpc, vision=False)
            elif (
                isinstance(ast.obj, list)
                and len(ast.obj) == 2
                and ast.obj[0] == "client"
            ):
                obj = self.proxy(self.rpc, ast.obj[1], vision=False)
            else:
                raise TypeError(f"obj type error: {ast.obj}")
            if ast.method is None or ast.obj is None:
                return obj
            if ast.args is not None:
                if (
                    len(ast.args) == 1
                    and ast.method == "__getattr__"
                    and isinstance(ast.args[0], str)
                ):
                    return getattr(obj, ast.args[0])
            func = getattr(obj, ast.method)
            if ast.args is None and ast.kwargs is None:
                return func
            if ast.method == "__anext__":
                return await func()

            args = []
            kwargs = {}
            for i in ast.args or ():
                args.append(await self.run(i))
            if ast.kwargs:
                for k, v in ast.kwargs.items():
                    kwargs[k] = await self.run(v)
            args = tuple(args)

            if ast.method == "__call__" and asyncio.iscoroutinefunction(obj):
                return await func(*args, **kwargs)
            elif asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            elif isinstance(obj, self.proxy):
                return func(*args, **kwargs)
            return func(*args, **kwargs)
        elif isinstance(ast, self.proxy):
            return await ast
        elif isinstance(ast, self.proxyresult):
            return ast.visions
        elif isinstance(ast, (list, tuple)):
            t_args = []
            for i in ast:
                t_args.append(await self.run(i))
            return type(ast)(t_args)
        elif isinstance(ast, dict):
            return {k: await self.run(v) for k, v in ast.items()}
        else:
            return ast


class Standard(BaseStandard[dict, JsonAst]):
    _jsonrpc = "jsonast"

    datatrans: Type[JsonAst] = JsonAst
    runtime: Type[RunTime] = RunTime
