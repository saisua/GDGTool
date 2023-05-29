from Core.Crawler import Crawler as Core_Crawler

from API.Browser import Browser

from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext

import asyncio
import cython
import traceback

class Crawler(Core_Crawler):
    _cr_inited: bool
    _cr_verbose: bool

    def __init__(self, *args, **kwargs):
        self._cr_inited = False
        self._cr_verbose = kwargs.get('verbose', False)
        
        args = list(args)
        sites = sargkwarg(0, "sites", dict, dict, args, kwargs)
        for site_list in sites:
            assert isinstance(site_list, list), "All domains must contain a list"

            for site_url in site_list:
                check_valid_url(site_url)

        super().__init__(*args, **kwargs)

    async def __aenter__(self, *args, **kwargs) -> object:
        await self.open_crawler()

        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close_crawler()

    async def open_crawler(self):
        if(self._cr_verbose):
            print("Open crawler", flush=False)
        try:
            await super().__aenter__()
        except Exception:
            print(traceback.format_exc())

        self._cr_inited = True

    async def close_crawler(self):
        if(self._cr_verbose):
            print("Close crawler", flush=False)
        try:
            self.check_crawler_inited()

            await super().__aexit__()
        except Exception:
            print(traceback.format_exc())

        self._cr_inited = False

    async def get_context(self, *args, **kwargs):
        if(self._cr_verbose):
            print("Get context", flush=False)
        
        try:
            self.check_crawler_inited()
            assert self.browser is not None, "[-] Browser has not been created"

            if(len(self.browser.contexts)):
                return self.browser.contexts[-1]
            else:
                if(self._cr_verbose):
                    print(" Creating new context", flush=False)
                return await self._new_context(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())

    async def open_websites(self, *args, **kwargs) -> object:
        if(self._cr_verbose):
            print("Open websites", flush=False)

        try:
            self.check_crawler_inited()
            args = list(args)

            context = await argkwarg(0, "context", BrowserContext, self.get_context, args, kwargs, force_async=True)
            websites = await argkwarg(1, "websites", set, set, args, kwargs, force_type=True)
            
            assert context is not None, "[-] Context has not been created"
            for website in websites:
                check_valid_url(website)

            if(self._cr_verbose):
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


    async def start_open_tabs(self, *args, **kwargs) -> cython.void:
        try:
            self.check_crawler_inited()

            args = list(args)
            await argkwarg(0, "num_tabs", int, lambda : 25, args, kwargs)
            await argkwarg(1, "context", BrowserContext, self._new_context, args, kwargs)

            return await super().start_open_tabs(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())

    async def get_tabs(self, *args, **kwargs) -> list:
        if(self._cr_verbose):
            print("Get websites", flush=False)
            
        try:
            self.check_crawler_inited()

            args = list(args)
            await argkwarg(0, "max_tabs", int, lambda : 25, args, kwargs)

            return await super().get_tabs(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())

    async def add_sites(self, *args, **kwargs):
        if(self._cr_verbose):
            print("Add sites", flush=False)

        try:
            self.check_crawler_inited()

            args = list(args)
            sites = await argkwarg(0, "sites", list, None, args, kwargs)

            for site in sites:
                assert isinstance(site, str), "All added sites must be strings"
                check_valid_url(site)

            if(self._cr_verbose):
                print(f"Add sites:", flush=False)
                sstr = '\n '.join(sites)
                print(f" {sstr}", flush=False)

            return await super().add_sites(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())

    async def crawl(self, *args, **kwargs) -> object:
        try:
            self.check_crawler_inited()

            args = list(args)
            contexts = await argkwarg(0, "contexts", list, lambda : [], args, kwargs)

            for context in contexts:
                assert isinstance(context, BrowserContext), "All contexts must be instances of BrowserContext"

            levels = await argkwarg(1, "levels", int, lambda : 0, args, kwargs)
            num_contexts = await argkwarg(None, "num_contexts", int, lambda : 3, args, kwargs)
            max_tabs = await argkwarg(None, "max_tabs", int, lambda : 25, args, kwargs)

            assert levels >= 0
            assert num_contexts > 0
            assert max_tabs > 0

            return await super().crawl(*args, **kwargs)
        except Exception:
            print(traceback.format_exc())

    def check_crawler_inited(self):
        assert self._cr_inited, "The crawler is not open yet"
