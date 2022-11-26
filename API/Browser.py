from Core.Browser import Browser as Core_Browser
from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext

import asyncio
import cython

class Browser(Core_Browser):
    _br_inited: bool

    

    def __init__(self, *args, **kwargs) -> None:
        self._br_inited = False
        Core_Browser.__init__(self, *args, **kwargs)

    async def open_browser(self):
        await Core_Browser.__aenter__(self)

        self._br_inited = True

    async def close_browser(self):
        self.check_browser_inited()

        await Core_Browser.__aexit__(self, )

        self._br_inited = False

    async def open_websites(self, *args, **kwargs) -> object:
        self.check_browser_inited()
        args = list(args)

        print(args, kwargs)
        await argkwarg(0, "context", BrowserContext, self.new_context, args, kwargs, force_async=True)
        websites = await argkwarg(1, "websites", set, set, args, kwargs, force_type=True)
        for website in websites:
            self.check_valid_url(website)

        print(f"open websites {args}, {kwargs}")
        if(kwargs.get("load_wait", True)):
            async for website in Core_Browser.open_websites(self, *args, **kwargs):
                yield website
        else:
            await Core_Browser.open_websites(self, *args, **kwargs)

    async def load_session(self, *args, context: object = None, load_wait: bool = False, **kwargs) -> object:
        self.check_browser_inited()
        args = list(args)

        await argkwarg(0, "session_name", str, None, args, kwargs)
        await argkwarg(None, "context", BrowserContext, None, args, kwargs, can_be_none=True)

        return await Core_Browser.load_session(self, *args, **kwargs)    
        

    async def search(self, *args, **kwargs):
        self.check_browser_inited()

        args = list(args)
        keywords = await argkwarg(0, "keywords", list, None, args, kwargs)
        await argkwarg(1, "search_in", str, lambda : "default", args, kwargs)
        search_in = await argkwarg(2, "block_start_domains", bool, lambda : True, args, kwargs)

        assert all((True for kw in keywords if type(kw) == str)), "All search keywords must be strings"
        assert all(keywords), "All search keywords must not be empty"
        #assert search_in in self.valid_search_contexts, "The search context is not valid"

        return await Core_Browser.search(self, *args, **kwargs)
    
    # Checks 

    def check_valid_url(self, url):
        assert isinstance(url, str), f"URL \"{url}\" must be a string"
        assert url_re.match(url), f"URL \"{url}\" is not valid"

    def check_browser_inited(self):
        assert self._br_inited, "The browser is not open yet"