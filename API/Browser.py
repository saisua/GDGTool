from Core.Browser import Browser as Core_Browser
from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext

import traceback

class Browser(Core_Browser):
    _br_inited: bool
    _br_verbose: bool  

    def __init__(self, *args, **kwargs) -> None:
        self._br_inited = False
        self._br_verbose = kwargs.get('verbose', False)
        super().__init__(*args, **kwargs)

    async def __aenter__(self, *args, **kwargs) -> object:
        await self.open_browser()

        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close_browser()

    async def open_browser(self):
        if(self._br_verbose):
            print("Open browser", flush=False)
        
        try:
            await super().__aenter__()
        except Exception:
            print(traceback.format_exc())

        self._br_inited = True

    async def close_browser(self):
        if(self._br_verbose):
            print("Close browser", flush=False)

        try:
            self.check_browser_inited()

            await super().__aexit__()
        except Exception:
            print(traceback.format_exc())

        self._br_inited = False

    async def get_context(self, *args, **kwargs):
        if(self._br_verbose):
            print("Get context", flush=False)
        
        try:
            self.check_browser_inited()
            assert self.browser is not None, "[-] Browser has not been created"

            if(len(self.browser.contexts)):
                return self.browser.contexts[-1]
            else:
                if(self._br_verbose):
                    print(" Creating new context", flush=False)
                return await self._new_context(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())

    async def open_websites(self, *args, **kwargs) -> object:
        if(self._br_verbose):
            print("Open websites", flush=False)

        try:
            self.check_browser_inited()
            args = list(args)

            context = await argkwarg(0, "context", BrowserContext, self.get_context, args, kwargs, force_async=True)
            websites = await argkwarg(1, "websites", set, set, args, kwargs, force_type=True)
            
            assert context is not None, "[-] Context has not been created"
            for website in websites:
                check_valid_url(website)

            if(self._br_verbose):
                wstr = '\n '.join(websites)
                print("Open websites:", flush=False)
                print(f" {wstr}", flush=False)

            if(kwargs.get("load_wait", True)):
                async for website in super()._open_websites(*args, **kwargs):
                    yield website
            else:
                yield super()._open_websites(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())

    async def load_session(self, *args, context: object = None, load_wait: bool = False, **kwargs) -> object:
        if(self._br_verbose):
            print("Load session", flush=False)

        try:
            self.check_browser_inited()
            args = list(args)

            await argkwarg(0, "session_name", str, None, args, kwargs)
            await argkwarg(None, "context", BrowserContext, None, args, kwargs, can_be_none=True)

            return await super().load_session(*args, **kwargs) 
        except Exception:
            print(traceback.format_exc())
        
    async def search(self, *args, **kwargs):
        if(self._br_verbose):
            print("Search", flush=False)

        try:
            self.check_browser_inited()

            args = list(args)
            keywords = await argkwarg(0, "keywords", (list, str), None, args, kwargs)
            await argkwarg(1, "search_in", str, lambda : "default", args, kwargs)
            search_in = await argkwarg(2, "block_start_domains", bool, lambda : True, args, kwargs)

            assert type(keywords) == str or all((True for kw in keywords if type(kw) == str)), "All search keywords must be strings"
            assert all(keywords), "All search keywords must not be empty"
            #assert search_in in self.valid_search_contexts, "The search context is not valid"

            if(self._br_verbose):
                print(f" search for: {keywords}", flush=False)

            links = await self._search.search(*args, **kwargs)
            if(kwargs.get("open_links", True)):
                context = await self.get_context()
                async for agen in self._open_websites(context, websites=set(links), load_wait=False):
                    async for _ in agen:
                        await _
        except Exception:
            print(traceback.format_exc())
    
    # Checks 

    def check_browser_inited(self):
        assert self._br_inited, "The browser is not open yet"