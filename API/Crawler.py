
from API.Browser import Browser as API_Browser
from Core.Crawler import Crawler as Core_Crawler

from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext


import asyncio
import cython

class Crawler(API_Browser, Core_Crawler):
    _cr_inited: bool
    _cr_verbose: bool

    def __init__(self, *args, **kwargs):
        self._cr_inited = False
        self._cr_verbose = kwargs.get('verbose', False)
        
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
        if(self._cr_verbose):
            print("Open crawler", flush=False)
        try:
            await API_Browser.open_browser(self)
            await Core_Crawler.__aenter__(self)
        except Exception as err:
            print(err)
            return err

        self._cr_inited = True

    async def close_crawler(self):
        if(self._cr_verbose):
            print("Close crawler", flush=False)
        try:
            self.check_crawler_inited()

            await API_Browser.close_browser(self)
            await Core_Crawler.__aexit__(self, )
        except Exception as err:
            print(err)
            return err

        self._cr_inited = False
    
    async def start_open_tabs(self, *args, **kwargs) -> cython.void:
        try:
            self.check_crawler_inited()

            args = list(args)
            await argkwarg(0, "num_tabs", int, lambda : 25, args, kwargs)
            await argkwarg(1, "context", BrowserContext, self.new_context, args, kwargs)

            return await Core_Crawler.start_open_tabs(self, *args, **kwargs)
        except Exception as err:
            print(err)
            return err

    async def get_websites(self, *args, **kwargs) -> list:
        if(self._cr_verbose):
            print("Get websites", flush=False)
        
        try:
            self.check_crawler_inited()

            args = list(args)
            await argkwarg(0, "max_tabs", int, lambda : 25, args, kwargs)

            return await Core_Crawler.get_websites(self, *args, **kwargs)
        except Exception as err:
            print(err)
            return err

    async def add_sites(self, *args, **kwargs):
        if(self._cr_verbose):
            print("Add sites", flush=False)

        try:
            self.check_crawler_inited()

            args = list(args)
            sites = await argkwarg(0, "sites", list, None, args, kwargs)

            for site in sites:
                assert isinstance(site, str), "All added sites must be strings"
                API_Browser.check_valid_url(site)

            if(self._cr_verbose):
                print(f"Add sites:", flush=False)
                sstr = '\n '.join(sites)
                print(f" {sstr}", flush=False)

            return await Core_Crawler.add_sites(self, *args, **kwargs)
        except Exception as err:
            print(err)
            return err

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

            return await Core_Crawler.crawl(self, *args, **kwargs)
        except Exception as err:
            print(err)
            return err

    def check_crawler_inited(self):
        assert self._cr_inited, "The crawler is not open yet"