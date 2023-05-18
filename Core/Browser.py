# distutils: language=c++

import asyncio
import cython
from playwright._impl._browser import Browser as _Browser
from playwright.async_api import async_playwright
from undetected_playwright import stealth_async

from Core.Storage import Storage
from Core.Pipeline import Pipeline
from Core.Session import Session
from Core.Resources import Resources
from Extensions.Search import Search

from Core.utils.children import Children

from Extensions.Rotating_proxies import Rotating_proxies
from Extensions import Macros


class Browser(Children):
    _storage: Storage
    _pipeline: Pipeline
    _session: Session
    _resources: Resources
    _rotating_proxies: Rotating_proxies
    _search: Search

    __playwright_instance: object
    _playwright_manager: object

    browser: _Browser

    browser_headless: cython.bint
    browser_name: str
    browser_persistent: cython.bint
    browser_install_addons: cython.bint

    _browser_use_proxies: cython.bint
    _browser_closed: cython.bint
    _browser_disconected: cython.bint

    Browser_init: cython.bint
    Browser_enter: cython.bint

    _browser_open_wait_until: str

    def __init__(self, *args, **kwargs) -> None:
        if(self.Browser_init):
            return 
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Browser")
        kwargs['verbose_depth'] = kwargs.get('verbose_depth', 0) + 1

        self.browser_headless = kwargs.pop("headless", True)
        self.browser_name = kwargs.pop("browser_name", "chromium")
        self.browser_persistent = kwargs.pop("browser_persistent", False)
        self.browser_install_addons = kwargs.pop("install_addons", True)

        self.__playwright_instance = None
        self._playwright_manager = None
        self.browser = None
        self._browser_use_proxies = False
        self._browser_closed = True
        self._browser_disconected = True
        self._browser_open_wait_until = kwargs.get("open_wait_until") or (
            "networkidle" if self.browser_install_addons else "load"
        )

        if(kwargs.get("use_resources", True)):
            self._resources = Resources(*args, **kwargs)
        else:
            self._resources = None
        if(kwargs.get("use_storage", True)):
            self._storage = Storage(self, remove_old_data=kwargs.pop("remove_old_data", False), folder_name=kwargs.pop("storage_name", None), **kwargs)
        else:
            self._storage = None
        if(kwargs.get("use_session", True)):
            self._session = Session(self, *args, **kwargs)
        else:
            self._session = None
        if(kwargs.get("use_pipeline", True)):
            self._pipeline = Pipeline(*args, **kwargs)
        else:
            self._pipeline = None
        if(kwargs.get("use_rotating_proxies", False)):
            self._rotating_proxies = Rotating_proxies(self, *args, **kwargs)
            self._browser_use_proxies = True
        else:
            self._rotating_proxies = None
            self._browser_use_proxies = False
        if(kwargs.get("use_search", True)):
            self._search = Search(self, *args, **kwargs)
        else:
            self._search = None
        self.Browser_init = True
        self.Browser_enter = False

        super().__init__((self._storage, self._pipeline, self._session, self._resources, self._rotating_proxies, self._search))

    async def __aenter__(self, *args, step:cython.bint=0, **kwargs) -> object:
        if(self.Browser_enter):
            return
        await self.open(*args, step=step, **kwargs)

        print("[+] Browser set up")
        return self

    async def __aexit__(self, *args, step:cython.bint=1, **kwargs) -> None:
        await self.close(*args, step=step, **kwargs)

    async def open(self, *args, step:cython.bint=0, **kwargs) -> None:
        if(not self.Browser_init): return
        if(step != 0): return

        self.Browser_enter = True

        await asyncio.create_task(super().__aenter__(self, *args, step=0, **kwargs))

        if(self.__playwright_instance is None):
            self.__playwright_instance = async_playwright()
        if(self._playwright_manager is None):
            self._playwright_manager = await self.__playwright_instance.__aenter__()

        if(self.browser is None):
            dyn_kwargs:dict = {}
            args:list = []
            if(self._browser_use_proxies):
                dyn_kwargs["proxy"]={"server": "per-context"}

            if(self.browser_name == "firefox"):
                dyn_kwargs["firefox_user_prefs"] = {
                }
            elif(self.browser_name == "chromium"):
                args.extend((
                    #f"--disable-extensions-except=Settings/Addons/DuckDuckGo-Privacy-Essentials.crx",
                    f"--load-extension=Settings/Addons/DuckDuckGo-Privacy-Essentials.crx",
                ))

            if(self.browser_persistent):
                launch = "launch_persistent_context"
                dyn_kwargs["user_data_dir"] = f"Settings/Persistent/{self.browser_name}"
            else:
                launch = "launch"

            self.browser = await getattr(
                getattr(
                    self._playwright_manager,
                    self.browser_name
                ),
                launch
            )(
                args=args,
                headless=self.browser_headless,
                **dyn_kwargs
            )

            if(self.browser_install_addons):
                context = await self._new_context()

                macro_obj = getattr(Macros, self.browser_name, None)
                if(type(self.browser_install_addons) == str):
                    for macro in (fname for fname in dir(macro_obj) if self.browser_install_addons in fname):
                        await getattr(macro_obj, macro)(context)
                else:
                    for macro in (fname for fname in dir(macro_obj) if not fname.startswith('_')):
                        await getattr(macro_obj, macro)(context)

                await context.close()

            print(self.browser)
        else:
            print("Browser exists")

        if(self.Rotating_proxies_init):
            await self.get_proxies_online()
    
        #self.browser.on("disconnected", self.__disconnect)
            
        self._browser_closed = False
        self._browser_disconected = False

        await asyncio.create_task(super().__aenter__(self, *args, step=1, **kwargs))

    async def close(self, *args, step:cython.bint=1, **kwargs) -> None:
        if(not self.Browser_init): return
        if(step != 1): return

        await asyncio.create_task(super().__aexit__(*args, step=0, **kwargs))
        await asyncio.sleep(0.01)

        await self.browser.close()
        await self.__playwright_instance.__aexit__()
        
        self._browser_closed = True
        self.Browser_enter = False

        if(self.Pipeline_init):
            print("Running post pipeline:")
            for post_f in self._post_management:
                print(f" {post_f.__name__}")
                await post_f(self)

        await asyncio.create_task(super().__aexit__(*args, step=1, **kwargs))

    async def _new_context(self, *args:tuple, **kwargs:dict) -> object:
        context:object = await self.browser.new_context(*args, **kwargs)
        await stealth_async(context)

        if(self.Pipeline_init):
            event:str
            handler:object
            for (event, handler) in self._event_management:
                context.on(event, handler(self))
            route:str
            for (route, handler) in self._route_management:
                await context.route(route, handler(self))

        return context

    async def _open_websites(self, context:object, websites:set, override:cython.bint=True, load_wait:cython.bint=True) -> object:
        pages: list
        if(not override):
            pages = [(await context.new_page()) for _ in range(len(websites))]
        else:
            for _ in range(len(websites)-len(context.pages)):
                await context.new_page()
            pages = context.pages


        page:object
        site:str
        if(load_wait):
            for page in asyncio.as_completed([
                    page.goto(site, wait_until=self._browser_open_wait_until) 
                        for page, site in zip(pages, websites)
                    ]):
                yield page
        else:
            for page, site in zip(pages, websites):
                asyncio.create_task(page.goto(site, timeout=0, wait_until=self._browser_open_wait_until))

    async def load_session(self, session_name:str, *args, context:object=None, load_wait:bool=False, **kwargs) -> object:
        if(context is None):
            context = await self._new_context()

        session:set
        site:str
        if(load_wait):
            async for _ in self._open_websites(context, [site for session in (await super()._load_session(session_name)) for site in session], *args, load_wait=load_wait, **kwargs):
                await _
        else:
            await self._open_websites(context, [site for session in (await super()._load_session(session_name)) for site in session], *args, load_wait=load_wait, **kwargs)

        return context
    
    async def wait_until_closed(self) -> None:
        while(self.closed() != True):
            await asyncio.sleep(3)

    def __disconnect(self) -> None:
        self._browser_disconected = True
    
    @property
    def closed(self) -> cython.bint:
        return (self._browser_disconected and self._browser_closed) or not len(self.browser.contexts) or not sum(map(lambda x: len(x.pages), self.browser.contexts))
