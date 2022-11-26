# distutils: language=c++

import asyncio
import cython
from playwright.async_api import async_playwright
from undetected_playwright import stealth_async

from Core.Storage import Storage
from Core.Pipeline import Pipeline
from Core.Session import Session
from Core.Resources import Resources
from Extensions.Search import Search

from Core.utils.children import Children

from Extensions.Rotating_proxies import Rotating_proxies


class Browser(Children):
    _storage: Storage
    _pipeline: Pipeline
    _session: Session
    _resources: Resources
    _rotating_proxies: Rotating_proxies
    _search: Search

    __playwright_instance : object = None
    _playwright_manager : object = None

    browser : object = None

    browser_headless : cython.bint
    browser_name : str
    browser_persistent: cython.bint

    _browser_use_proxies : cython.bint = False
    _browser_closed : cython.bint = True

    Browser_init: cython.bint
    Browser_enter: cython.bint

    def __init__(self, *args, **kwargs) -> None:
        if(self.Browser_init):
            return 
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Browser")
        kwargs['verbose_depth'] = kwargs.get('verbose_depth', 0) + 1

        self.browser_headless = kwargs.pop("headless", True)
        self.browser_name = kwargs.pop("browser_name", "chromium")
        self.browser_persistent = kwargs.pop("browser_persistent", False)

        if(kwargs.pop("use_storage", True)):
            self._storage = Storage(remove_old_data=kwargs.pop("remove_old_data", False), folder_name=kwargs.pop("storage_name", None), **kwargs)
        else:
            self._storage = None
        if(kwargs.pop("use_pipeline", True)):
            self._pipeline = Pipeline(*args, **kwargs)
        else:
            self._pipeline = None
        if(kwargs.pop("use_session", True)):
            self._session = Session(self, *args, **kwargs)
        else:
            self._session = None
        if(kwargs.pop("use_resources", True)):
            self._resources = Resources(*args, **kwargs)
        else:
            self._resources = None
        if(kwargs.pop("use_rotating_proxies", False)):
            self._rotating_proxies = Rotating_proxies(self, *args, **kwargs)
            self._browser_use_proxies = True
        else:
            self._rotating_proxies = None
            self._browser_use_proxies = False
        if(kwargs.pop("use_search", True)):
            self._search = Search(self, *args, **kwargs)
        else:
            self._search = None
        self.Browser_init = True
        self.Browser_enter = False

        super().__init__((self._storage, self._pipeline, self._session, self._resources, self._rotating_proxies, self._search))

    async def __aenter__(self, *args, **kwargs) -> object:
        if(self.Browser_enter):
            return
        await Browser.open(self, *args, **kwargs)

        print("[+] Browser set up")
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close(*args, **kwargs)

    async def open(self, *args, **kwargs) -> None:
        if(not self.Browser_init): return

        self.Browser_enter = True

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
                #args.extend(("-start-debugger-server", "12345"))
                dyn_kwargs["firefox_user_prefs"] = {
                    'devtools.debugger.remote-enabled': True,
                    'devtools.debugger.prompt-connection': False,
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

            if(self.browser_name == "firefox"):
                # about:debugging#/runtime/this-firefox
                page = await self.browser.new_page()
                await page.goto("about:preferences#search", wait_until="domcontentloaded")
                await page.keyboard.press("Tab")
                await page.keyboard.press("Tab")
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("ArrowDown")
                await page.close()

            print(self.browser)
        else:
            print("Browser exists")

        if(self.Rotating_proxies_init):
            await self.get_proxies_online()
            
        self._browser_closed = False

        await super().__aenter__(*args, **kwargs)

    async def close(self, *args, **kwargs) -> None:
        if(not self.Browser_init): return

        if(self.Pipeline_init):
            for post_f in self._post_management:
                await post_f(self)

        await super().__aexit__(*args, **kwargs)

        await self.browser.close()
        await self.__playwright_instance.__aexit__()
        
        self._browser_closed = True
        self.Browser_enter = False

    async def new_context(self, *args:tuple, **kwargs:dict) -> object:
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

    async def open_websites(self, context:object, websites:set, override:cython.bint=True, load_wait:cython.bint=True, wait_until:str='networkidle') -> object:
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
            for page in asyncio.as_completed([page.goto(site, timeout=5000, wait_until=wait_until) for page, site in zip(pages, websites)]):
                yield page
        else:
            for page, site in zip(pages, websites):
                asyncio.create_task(page.goto(site, timeout=0, wait_until=wait_until))

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
    
    async def wait_until_closed(self) -> None:
        while(self.closed() != True):
            await asyncio.sleep(3)

    @property
    def closed(self) -> cython.bint:
        return self._browser_closed or not len(self.browser.contexts) or not sum(map(lambda x: len(x.pages), self.browser.contexts))
