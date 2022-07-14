from Core.Browser import Browser as Core_Browser
from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext

import asyncio
import cython

class Browser(Core_Browser):
    _inited = False
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def open(self):
        print(hasattr(self, "Browser_init"))
        await super().open()

        self._inited = True

    async def close(self):
        self.check_inited()

        await super().close()

        self._inited = False

    async def open_websites(self, *args, **kwargs) -> object:
        self.check_inited()

        argkwarg(0, "context", BrowserContext, self.new_context, *args, **kwargs)
        websites = argkwarg(1, "websites", None, set, *args, **kwargs)
        for website in websites:
            self.check_valid_url(website)

        if(kwargs.get("load_wait", True)):
            async for website in super().open_websites(*args, **kwargs):
                yield website
        else:
            await super().open_websites(*args, **kwargs)

    async def load_session(self, *args, context: object = None, load_wait: bool = False, **kwargs) -> object:
        self.check_inited()

        argkwarg(0, "session_name", str, None)
        argkwarg(None, "context", BrowserContext, None, *args, **kwargs, can_be_none=True)

        return await super().load_session(*args, **kwargs)    
        

    # Checks 

    def check_valid_url(self, url):
        assert isinstance(url, str), f"URL \"{url}\" must be a string"
        assert url_re.match(url), f"URL \"{url}\" is not valid"

    def check_inited(self):
        assert self._inited, "The browser is not open yet"