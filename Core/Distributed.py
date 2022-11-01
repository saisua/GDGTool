# distutils: language=c++

import asyncio
import cython
from inspect import iscoroutinefunction
from multiprocessing.managers import BaseManager
from multiprocessing import Manager

from Core.Browser import Browser
from Core.Crawler import Crawler

class Server(BaseManager, Crawler):
    _manager:object
    _loop:object

    _exposed:set = {"get_sites", "get_exposed", "_register", "get_crawler", "get_attr", "run_async"}
    def __init__(self, sites:dict={}, address=('localhost', 12412), authkey=b"None", *args, **kwargs):
        #Crawler.__init__(self, sites, *args, **kwargs)
        self._manager = Manager()
        self._loop = asyncio.get_event_loop()
        self.sites = self._manager.dict(sites)

        Crawler.__init__(self, *args, **kwargs)
        BaseManager.__init__(self, address=address, authkey=authkey)
        setattr(self, "Server_init", True)

    async def __aenter__(self, *args, **kwargs) -> object:
        for _ in asyncio.as_completed([cl.__aenter__(self) for cl in Server.__mro__ if cl != Server and hasattr(cl, "__aenter__")]):
            await _

        self.register("get_sites", self._get_sites)
        self.register("get_exposed", self._get_exposed)
        self.register("_register", self._register)
        self.register("get_crawler", self._get_crawler)
        self.register("get_attr", self._get_attr)
        self.register("run_async", self._run_async)

        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        for _ in asyncio.as_completed([cl.__aexit__(self, *args, **kwargs) for cl in Server.__mro__ if cl != Server and hasattr(cl, "__aexit__")]):
            await _

        

    def _get_sites(self):
        return self.sites
    def _get_exposed(self):
        return self._exposed
    def _get_crawler(self):
        return self
    def _get_attr(self, attr):
        return getattr(self, attr)

    def _run_async(self, f_name, *args, **kwargs):
        asyncio.run(getattr(self, f_name)(*args, **kwargs))

    def _register(self, f_name):
        if(f_name in self._exposed): return
        c_name = f"_{f_name}"
        self._exposed.add(c_name)        

        f = getattr(self, f_name)

        if(iscoroutinefunction(f)):
            def handle_f(*args, **kwargs):
                #asyncio.set_event_loop(self._loop)
                #return self._loop.run_until_complete(getattr(self, f_name)(*args, **kwargs))
                return asyncio.run_coroutine_threadsafe(getattr(self, f_name)(*args, **kwargs),self._loop).result()

            self.register(c_name, handle_f)
        else:
            self.register(c_name, f)

        print(f"Registered {'coroutine' if iscoroutinefunction(f) else ''} function {f_name}")



class Client(BaseManager):
    _exposed:set
    sited:dict
    crawler:Crawler

    def __init__(self, sites:dict={}, address=('localhost', 12412), authkey=b"None", *args, **kwargs):
        #Crawler.__init__(self, *args, **kwargs)
        BaseManager.__init__(self, address=address, authkey=authkey)
        setattr(self, "Client_init", True)

    async def __aenter__(self, *args, **kwargs) -> object:
        for _ in asyncio.as_completed([cl.__aenter__(self) for cl in Client.__mro__ if cl != Client and hasattr(cl, "__aenter__")]):
            await _

        ###
        retries:cython.uint = 0
        while(True):
            try:
                self.connect()
                break
            except (ConnectionRefusedError, ConnectionResetError):
                if(not retries):
                    print("Awaiting server...")
                retries += 1
                await asyncio.sleep(retries)
        ###

        self.register("get_exposed")
        Client._exposed = self.get_exposed()._getvalue()
    
        for server_func in Client._exposed:
            self.register(server_func)
    
        self.sites = self.get_sites()
        self.crawler = self.get_crawler()

        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        for _ in asyncio.as_completed([cl.__aexit__(self, *args, **kwargs) for cl in Client.__mro__ if cl != Client and hasattr(cl, "__aexit__")]):
            await _

        #self.join()
        #self.shutdown()

    def server_register(self, f_name:str, c_name:str=None):
        self._register(f_name)
        Client._exposed.add(c_name or f_name)
        self.register(c_name or f_name)

    async def delegate(self, func_name:str, *args, **kwargs):
        call_name:str = f"_{func_name}"
        if(call_name not in Client._exposed):
            self.server_register(func_name, call_name)

        print(f"Delegate: {func_name}")
        getattr(self, call_name)(*args, **kwargs)