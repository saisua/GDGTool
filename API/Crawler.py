
from API.Browser import Browser as API_Browser
from Core.Crawler import Crawler as Core_Crawler

from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext


import asyncio
import cython

class Crawler(API_Browser, Core_Crawler):
    _cr_inited: bool = False

    def __init__(self, *args, **kwargs):
        args = list(args)
        sites = sargkwarg(0, "sites", dict, dict, args, kwargs)
        for site_list in sites:
            assert isinstance(site_list, list), "All domains must contain a list"

            for site in site_list:
                assert isinstance(site, str), "All urls must be strings"
                assert url_re.match(site), f"URL {site} is invalid" 

        API_Browser.__init__(self, *args, **kwargs)
        Core_Crawler.__init__(self, *args, **kwargs)

    async def open_crawler(self):
        await API_Browser.open_browser(self)
        await Core_Crawler.__aenter__(self, )

        self._cr_inited = True

    async def close_crawler(self):
        self.check_crawler_inited()

        await API_Browser.close_browser(self)
        await Core_Crawler.__aexit__(self, )

        self._cr_inited = False
    
    @cython.cfunc
    async def start_open_tabs(self, *args, **kwargs) -> cython.void:
        self.check_crawler_inited()

        args = list(args)
        await argkwarg(0, "num_tabs", int, lambda : 25, args, kwargs)
        await argkwarg(1, "context", BrowserContext, self.new_context, args, kwargs)

        return await Core_Crawler.start_open_tabs(self, *args, **kwargs)

    async def get_websites(self, *args, **kwargs) -> list:
        self.check_crawler_inited()

        args = list(args)
        await argkwarg(0, "max_tabs", int, lambda : 25, args, kwargs)

        return await Core_Crawler.get_websites(self, *args, **kwargs)

    async def add_sites(self, *args, **kwargs):
        self.check_crawler_inited()

        args = list(args)
        sites = await argkwarg(0, "sites", list, None, args, kwargs)

        for site in sites:
            assert isinstance(site, str), "All added sites must be strings"

        return await Core_Crawler.add_sites(self, *args, **kwargs)

    async def search(self, *args, **kwargs):
        self.check_crawler_inited()

        args = list(args)
        keywords = await argkwarg(0, "keywords", list, None, args, kwargs)
        await argkwarg(1, "search_in", str, lambda : "default", args, kwargs)
        search_in = await argkwarg(2, "block_start_domains", bool, lambda : True, args, kwargs)

        assert all((True for kw in keywords if type(kw) == str)), "All search keywords must be strings"
        assert all(keywords), "All search keywords must not be empty"
        assert search_in in self.valid_search_contexts, "The search context is not valid"

        return await Core_Crawler.search(self, *args, **kwargs)

    async def crawl(self, *args, **kwargs) -> object:
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

        return await Core_Crawler.crawl(self, *args, **kwargs)

    def check_crawler_inited(self):
        assert self._cr_inited, "The crawler is not open yet"