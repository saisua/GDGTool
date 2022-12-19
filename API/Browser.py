from Core.Browser import Browser as Core_Browser
from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext

import asyncio
import cython

class Browser(Core_Browser):
    _br_inited: bool
    _br_verbose: bool  

    def __init__(self, *args, **kwargs) -> None:
        self._br_inited = False
        self._br_verbose = kwargs.get('verbose', False)
        Core_Browser.__init__(self, *args, **kwargs)

    async def open_browser(self):
        if(self._br_verbose):
            print("Open browser", flush=False)
        
        try:
            await Core_Browser.__aenter__(self)
        except Exception as err:
            print(err)
            return err
        
        self._br_inited = True

    async def close_browser(self):
        if(self._br_verbose):
            print("Close browser", flush=False)

        try:
            self.check_browser_inited()

            await Core_Browser.__aexit__(self, )
        except Exception as err:
            print(err)
            return err

        self._br_inited = False

    async def get_context(self, *args, **kwargs):
        if(self._br_verbose):
            print("Get context", flush=False)
        
        try:
            self.check_browser_inited()

            if(len(self.browser.contexts)):
                return self.browser.contexts[-1]
            else:
                if(self._br_verbose):
                    print(" Creating new context", flush=False)
                return await self.new_context(*args, **kwargs)
        except Exception as err:
            print(err)
            return err

    async def open_websites(self, *args, **kwargs) -> object:
        if(self._br_verbose):
            print("Open websites", flush=False)

        try:
            self.check_browser_inited()
            args = list(args)

            await argkwarg(0, "context", BrowserContext, self.get_context, args, kwargs, force_async=True)
            websites = await argkwarg(1, "websites", set, set, args, kwargs, force_type=True)
            for website in websites:
                Browser.check_valid_url(website)
            if(self._br_verbose):
                wstr = '\n '.join(websites)
                print("Open websites:", flush=False)
                print(f" {wstr}", flush=False)

            if(kwargs.get("load_wait", True)):
                async for website in Core_Browser.open_websites(self, *args, **kwargs):
                    yield website
            else:
                yield Core_Browser.open_websites(self, *args, **kwargs)
        except Exception as err:
            print(err)

    async def load_session(self, *args, context: object = None, load_wait: bool = False, **kwargs) -> object:
        if(self._br_verbose):
            print("Load session", flush=False)

        try:
            self.check_browser_inited()
            args = list(args)

            await argkwarg(0, "session_name", str, None, args, kwargs)
            await argkwarg(None, "context", BrowserContext, None, args, kwargs, can_be_none=True)

            return await Core_Browser.load_session(self, *args, **kwargs) 
        except Exception as err:
            print(err)
            return err   
        
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
                async for agen in self.open_websites(context, websites=set(links), load_wait=False):
                    async for _ in agen:
                        await _
        except Exception as err:
            print(err)
            return err
    
    # Checks 

    @staticmethod
    def check_valid_url(url):
        assert isinstance(url, str), f"URL \"{url}\" must be a string"
        assert url_re.match(url), f"URL \"{url}\" is not valid"

    def check_browser_inited(self):
        assert self._br_inited, "The browser is not open yet"