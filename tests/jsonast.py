import asyncio

from lacia.logger import logger
from lacia.standard.jsonast.runtime import RunTime, Standard, Namespace, JsonAst
from lacia.core.proxy import ProxyObj, ResultProxy


async def test_aping(x):
    return f"pong: {x}"


async def test_async_iter(n):
    for i in range(n):
        await asyncio.sleep(1)
        yield i


class TestJson:
    def __init__(self, a, b=1, c: dict = {}) -> None:
        self.a = a
        self.b = b
        self.c = c

    def sum(self):
        return self.a + self.b

    def test_return(self, text):
        return f"return: {text}"


namespace = {
    "test_attribute": "Hello World!",
    "test_ping": lambda x: f"pong: {x}",
    "test_aping": test_aping,
    "test_class_init": TestJson,
    "test_async_iter": test_async_iter,
    "Test": TestJson,
}
#  嵌套


class Test:
    async def test_attribute(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        obj = ProxyObj()

        astboj = obj.test_attribute._obj

        r = await runtime.run(astboj)

        assert r == "Hello World!"

    async def test_ping(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        obj = ProxyObj()

        astboj = obj.test_ping("hello")._obj

        r = await runtime.run(astboj)

        assert r == "pong: hello"

    async def test_aping(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        obj = ProxyObj()

        astboj = obj.test_aping("hello")._obj

        r = await runtime.run(astboj)

        assert r == "pong: hello"

    async def test_class_init(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        obj = ProxyObj()

        astboj = obj.test_class_init(1, b=3).sum()._obj

        r = await runtime.run(astboj)

        assert r == 4

    async def test_class_attribute(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        obj = ProxyObj()

        astobj = obj.test_class_init(1, b=3).a._obj

        r = await runtime.run(astobj)

        assert r == 1

    async def test_object_nest(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        a_obj = ProxyObj().test_ping("ping")
        b_obj = ProxyObj().test_class_init(1, b=3).test_return(a_obj)
        c_obj = ProxyObj()

        astobj = c_obj.test_ping(b_obj)._obj

        r = await runtime.run(astobj)

        assert r == "pong: return: pong: ping"

    async def test_getattr(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        obj = getattr(ProxyObj(), "test_ping")("ping")

        astobj = obj._obj

        r = await runtime.run(astobj)

        assert r == "pong: ping"

    async def test_loads_dumps(self):
        runtime = Standard.runtime(namespace, ProxyObj, ResultProxy)
        obj = ProxyObj()

        astobj = obj.Test(1, b=2, c={"c": 3})._obj

        astobj = JsonAst.loads(JsonAst.dumps(astobj))

        r = await runtime.run(astobj)

        assert r.c == {"c": 3}

    async def main(self):
        for func in dir(self):
            if func.startswith("test_"):
                await getattr(self, func)()
                logger.success(f"{func} passed")


async def main():
    await Test().main()


asyncio.run(main())
