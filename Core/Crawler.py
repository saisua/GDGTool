# distutils: language=c++

import asyncio
from multiprocessing.connection import wait
import re
import cython
import multiprocessing as mp
from typing import *
from itertools import chain
from xml import dom
from math import ceil

from playwright.async_api import TimeoutError

from Core.Browser import Browser
from Extensions.Search import Search

@cython.cclass
class Crawler(Browser, Search):
    sites : dict # Dict[str, List[str]]
    next_level_sites : dict # Dict[str, List[str]]

    _avaliable_tabs : list
    _open_tabs : int

    visited_urls : set # Set[str]
    blocked_domains : set # Set[str]

    website_data : dict

    # Regex to find the domain of a URL. 
    # per example: https://desktop.github.com/test -> github.com
    domain_regex : re.Pattern = re.compile(r"^(https?://)?([^/]+\.)?([^/]+\.[^/]+).*")

    def __init__(self, sites:Dict[str, List[str]]={}, *args:tuple, **kwargs:dict):
        if(kwargs.pop("use_browser", True)):
            Browser.__init__(self, *args, **kwargs)
        if(kwargs.pop("use_search", True)):
            Search.__init__(self, self, *args, **kwargs)

        self.sites = sites
        self.visited_urls = kwargs.pop("visited_urls", set())
        self.blocked_domains = kwargs.pop("blocked_domains", set())
        self.add_pipe("page", Crawler.get_urls, "Get all URLs (necessary for crawling)")

        self._avaliable_tabs = []
        self._open_tabs = 0

        self.next_level_sites = dict()
        setattr(self, "Crawler_init", True)


    @cython.cfunc
    async def start_open_tabs(self, num_tabs:cython.uint, context:object) -> cython.void:
        self._avaliable_tabs.extend([await context.new_page() for _ in range(num_tabs)])
        self._open_tabs += num_tabs

    @cython.inline
    @cython.cdivision(True)
    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cfunc
    async def get_websites(self, max_tabs:cython.uint) -> list:
        # To be overridden when using a distributed crawler
        next_tabs:list = self._avaliable_tabs[:max_tabs]

        if(not len(next_tabs)):
            while(True):
                # Wait until at least one tab has finished
                await asyncio.sleep(1)

                if(len(self._avaliable_tabs)):
                    next_tabs[:max_tabs]
                    break

        self._avaliable_tabs = self._avaliable_tabs[len(next_tabs):]

        return next_tabs
            
    @cython.cfunc
    async def add_sites(self, sites:list):
        site:str
        for site in sites:
            match:object = self.domain_regex.search(site)
            if(match):
                domain:str = match.group(3)
                if(domain not in self.sites):
                    self.sites[domain] = {site}
                else:
                    self.sites.get(domain).add(site)

    @cython.inline
    @cython.cdivision(True)
    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cfunc
    async def _manage_website(self, tab:object, url:str):
        loaded_site:object = await tab.goto(url, wait_until="networkidle")

        while(loaded_site is None):
            loaded_site = await tab.goto(url, wait_until="networkidle")

        loaded_site.domain = self.domain_regex.match(loaded_site.url).group(3)

        website_data:dict = {}
        repeat:cython.bint = True
        # In case of dynamically loaded websites
        for _ in asyncio.as_completed([page_alter(self, website_data, loaded_site) for page_alter in self._page_management]):
            await _
        for _ in asyncio.as_completed([data_alter(self, website_data, loaded_site) for data_alter in self._data_management]):
            await _

        if("urls" in website_data):
            site:str
            for site in website_data["urls"]:
                if(site not in self.visited_urls):
                    self.visited_urls.add(site)

                    match:object = self.domain_regex.search(site)
                    if(match):
                        domain:str = match.group(3)
                        if(domain not in self.blocked_domains):
                            if(domain not in self.sites):
                                self.next_level_sites[domain] = {site}
                            else:
                                self.next_level_sites[domain].add(site)
        
        asyncio.create_task(self.add_data(loaded_site.domain, (loaded_site.url, website_data)))
            
        self._avaliable_tabs.append(tab)

    @cython.inline
    @cython.cdivision(True)
    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cfunc
    async def get_crawling_urls(self, num_tabs:cython.uint) -> list:
        result:list = []
        end_domains:list = []
        n_domains:cython.uint = len(self.sites)
        added_websites:cython.uint
        _:cython.uint\

        domain_n:str
        domain_l:list
        added_websites:cython.uint
        for domain_n, domain_l in self.sites.items():
            added_websites = int((num_tabs - len(result)) / n_domains) or 1
            if(added_websites >= len(domain_l)):
                end_domains.append(domain_n)
                result.extend(domain_l)
            else:
                for _ in range(added_websites):
                    result.append(domain_l.pop())

            if(len(result) >= num_tabs):
                break
            n_domains -= 1

        domain:str
        for domain in end_domains:
            self.sites.pop(domain)

        return result

    @cython.inline
    @cython.cdivision(True)
    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cfunc
    async def crawl(self, contexts:list=[], levels:cython.uint=0, *, num_contexts:cython.uint=3, max_tabs:cython.uint=25, close_contexts:cython.bint=False) -> object:
        if(not contexts):
            print(num_contexts)
            _:cython.uint
            dyn_attr:dict = {}
            for _ in range(num_contexts):
                print(_)
                if(hasattr(self, "Rotating_proxies_init")):
                    dyn_attr["proxy"] = {"server":self.new_proxy()}
                print(dyn_attr)

                nc = await self.new_context(
                                                        accept_downloads=False,
                                                        **dyn_attr
                                                    )
                print(nc)
                contexts.append(nc)
                print("Added")
            close_contexts = True

        print("Start")
        for start_f in self._start_management:
            await start_f(self, context)
            
        print("End start")
        self.visited_urls.update(chain(*self.sites.values()))

        print("Context")
        context:object
        tabs_per_context:cython.uint = ceil(max_tabs / num_contexts)
        for context in contexts:
            await self.start_open_tabs(tabs_per_context, context)

        tabs:list = []
        urls:list = []
        level:cython.uint
        for level in range(levels+1):
            print(f"\n\n# Level {level}:")
            while(len(self.sites)):
                print(f"  Found {len(self.visited_urls)} websites", end='\r')

                tabs = await self.get_websites(max_tabs)
                urls = await self.get_crawling_urls(len(tabs))
                
                if(len(urls) != len(tabs)):
                    self._avaliable_tabs.extend(tabs[len(urls):])

                if(self._url_management):
                    altered_urls = set()
                    for alter_url in self._url_management:
                        altered_urls.update(await alter_url(self, urls))
                    
                    urls = altered_urls

                for tab, url in zip(tabs, urls):
                    asyncio.create_task(self._manage_website(tab, url))
                    
            # Wait until all tabs have finished
            # This is so that next_level_sites is complete
            #  otherwise, some sites may mix into the next depth level
            retries = 40
            while(len(self._avaliable_tabs) != self._open_tabs and retries):
                await asyncio.sleep(1)
                retries -= 1

            self.sites.clear()
            self.sites.update(self.next_level_sites)

        for context in contexts:
            for end_f in self._end_management:
                await end_f(self, context)

            if(close_contexts):
                await context.close()
        
        return contexts

    @staticmethod
    @cython.cfunc
    async def get_urls(self, data:dict, page:object):
        links:list = await page.frame.locator(":link:not(:visited)").evaluate_all("nodes => nodes.map(node => node.href)")
        if(links is not None):
            data["urls"] = set(links)

    @staticmethod
    @cython.cfunc
    async def get_images(self, data:dict, page:object):
        images:list = await page.frame.locator("img[src]").evaluate_all("nodes => nodes.map(node => node.src)")
        while(not images):
            await asyncio.sleep(0.5)
            images = await page.frame.locator("img[src]").evaluate_all("nodes => nodes.map(node => node.src)")

            if(images is None):
                return 

        if(images is not None):
            data["images"] = set(images)

    @staticmethod
    @cython.cfunc
    async def get_videos(self, data:dict, page:object):
        videos:list = await page.frame.locator("video[src]").evaluate_all("nodes => nodes.map(node => node.src)")

        if(videos is not None):
            data["videos"] = set(videos)

    @staticmethod
    @cython.cfunc
    async def get_text(self, data:dict, page:object):
        text:str = await page.frame.evaluate("document.body.innerText")
        
        if(text is not None):
            data["text"] = text

    @staticmethod
    @cython.ccall
    async def load_session(self, session_name:str, *args, **kwargs) -> None:
        await self.add_sites((site for session in (await super()._load_session(session_name)) for site in session))

    @staticmethod
    @cython.ccall
    def block_resources(crawler:object):
        @cython.cfunc
        async def _block_resources(route:object):
            if(route.request.resource_type not in {"fetch", "script", "document"}):
                #print(f"Blocked resource: {route.request.resource_type}")
                await route.abort()
            else:
                await route.continue_()
        return _block_resources