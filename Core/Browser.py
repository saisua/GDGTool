# distutils: language=c++

import asyncio
import cython
from itertools import chain

from playwright.async_api import async_playwright

from Core.Storage import Storage
from Core.Pipeline import Pipeline
from Core.Session import Session
from Core.Resources import Resources

from Extensions.Rotating_proxies import Rotating_proxies

@cython.cclass
class Browser(Storage, Pipeline, Session, Resources, Rotating_proxies):
    __playwright_instance : object = None
    _playwright_manager : object = None

    browser : object = None

    headless : cython.bint = True
    browser_name : str

    _use_proxies : cython.bint = False
    _closed : cython.bint = True

    def __init__(self, *args, **kwargs) -> None:
        self.headless = kwargs.pop("headless", self.headless)
        self.browser_name = kwargs.pop("browser_name", "chromium")

        if(kwargs.pop("use_storage", True)):
            Storage.__init__(self, kwargs.pop("remove_old_data", False))
        if(kwargs.pop("use_pipeline", True)):
            Pipeline.__init__(self)
        if(kwargs.pop("use_session", True)):
            Session.__init__(self, self, *args, **kwargs)
        if(kwargs.pop("use_resources", True)):
            Resources.__init__(self, *args, **kwargs)
        if(kwargs.pop("use_rotating_proxies", False)):
            Rotating_proxies.__init__(self, self, *args, **kwargs)
            self._use_proxies = True
        setattr(self, "Browser_init", True)

    async def __aenter__(self, *args, **kwargs) -> object:
        for _ in asyncio.as_completed([self.open(*args, **kwargs), *[cl.__aenter__(self) for cl in Browser.__mro__ if cl != Browser and hasattr(cl, "__aenter__")]]):
            await _

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        for _ in asyncio.as_completed([cl.__aexit__(self, exc_type, exc_val, exc_tb) for cl in Browser.__mro__ if cl != Browser and hasattr(cl, "__aexit__")]):
            await _
        await self.close()

    async def open(self) -> None:
        print(hasattr(self, "Browser_init"))
        if(not hasattr(self, "Browser_init")): return

        if(self.__playwright_instance is None):
            self.__playwright_instance = async_playwright()
        if(self._playwright_manager is None):
            self._playwright_manager = await self.__playwright_instance.__aenter__()

        if(self.browser is None):
            dyn_kwargs:dict = {}
            if(self._use_proxies):
                dyn_kwargs["proxy"]={"server": "per-context"}
                                                                                        
            self.browser = await getattr(self._playwright_manager, self.browser_name).launch(
                                                                                        headless=self.headless,
                                                                                        **dyn_kwargs
                                                                                        )

            print(self.browser)
        else:
            print("Browser exists")

        if(hasattr(self, "Rotating_proxies_init")):
            await self.get_proxies_online()
            
        self._closed = False

    async def close(self) -> None:
        if(not hasattr(self, "Browser_init")): return

        await self.browser.close()
        await self.__playwright_instance.__aexit__()
        await self.dump_all_data()
        
        self._closed = True

    @cython.cfunc
    async def new_context(self, *args:tuple, **kwargs:dict) -> object:
        context:object = await self.browser.new_context(*args, **kwargs)

        event:str
        handler:object
        for (event, handler) in self._event_management:
            context.on(event, handler(self))
        route:str
        for (route, handler) in self._route_management:
            await context.route(route, handler(self))

        return context

    @cython.inline
    @cython.cfunc
    async def open_websites(self, context:object, websites:set, override:cython.bint=True, load_wait:cython.bint=True) -> object:
        pages:list
        if(not override):
            pages = [(await context.new_page()) for _ in range(len(websites))]
        else:
            for _ in range(len(websites)-len(context.pages)):
                await context.new_page()
            pages = context.pages

        page:object
        site:str
        if(load_wait):
            for page in asyncio.as_completed([page.goto(site, timeout=5000) for page, site in zip(pages, websites)]):
                yield page
        else:
            for page, site in zip(pages, websites):
                asyncio.create_task(page.goto(site, timeout=0))

    @cython.ccall
    async def load_session(self, session_name:str, *args, context:object=None, load_wait:bool=False, **kwargs) -> object:
        if(context is None):
            context = await self.new_context()

        session:set
        site:str
        if(load_wait):
            async for _ in self.open_websites(context, [site for session in (await super()._load_session(session_name)) for site in session], *args, load_wait=load_wait, **kwargs):
                await _
        else:
            await self.open_websites(context, [site for session in (await super()._load_session(session_name)) for site in session], *args, load_wait=load_wait, **kwargs)

        return context

    @property
    def closed(self):
        return self._closed or not len(self.browser.contexts) or not sum(map(lambda x: len(x.pages), self.browser.contexts))