from ast import arg
from Core.Crawler import Crawler as Core_Crawler
from API.utils.function import *
from API.utils.url_utils import *

from playwright.async_api._generated import BrowserContext


import asyncio
import cython

class Crawler(Core_Crawler):
    def __init__(self, *args, **kwargs):
        sites = argkwarg(0, "sites", dict, dict, *args, **kwargs)
        for site_list in sites:
            assert isinstance(site_list, list), "All domains must contain a list"

            for site in site_list:
                assert isinstance(site, str), "All urls must be strings"
                assert url_re.match(site), f"URL {site} is invalid" 

        super().__init__(*args, **kwargs)

    
    @cython.cfunc
    async def start_open_tabs(self, *args, **kwargs) -> cython.void:
        argkwarg(0, "num_tabs", int, lambda : 25, *args, **kwargs)
        argkwarg(1, "context", BrowserContext, super().new_context, *args, **kwargs)

        return await super().start_open_tabs(*args, **kwargs)

    async def get_websites(self, *args, **kwargs) -> list:
        argkwarg(0, "max_tabs", int, lambda : 25, *args, **kwargs)

        return await super().get_websites(*args, **kwargs)

    async def add_sites(self, *args, **kwargs):
        sites = argkwarg(0, "sites", list, None, *args, **kwargs)

        for site in sites:
            assert isinstance(site, str), "All added sites must be strings"

        return await super().add_sites(*args, **kwargs)

    async def crawl(self, *args, **kwargs) -> object:
        contexts = argkwarg(0, "contexts", list, lambda : [], *args, **kwargs)

        for context in contexts:
            assert isinstance(context, BrowserContext), "All contexts must be instances of BrowserContext"

        argkwarg(1, "levels", int, lambda : 0, *args, **kwargs)
        argkwarg(None, "num_contexts", int, lambda : 3, *args, **kwargs)
        argkwarg(None, "max_tabs", int, lambda : 25, *args, **kwargs)

        return await super().crawl(*args, **kwargs)