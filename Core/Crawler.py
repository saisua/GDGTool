# distutils: language=c++

import asyncio
import re
import cython
from typing import *
from itertools import chain
from math import ceil
import numpy as np

from urllib.request import urlopen

from playwright.async_api import TimeoutError

from Core.Browser import Browser


class Crawler(Browser):
    crawler_sites: dict # Dict[str, List[str]]
    next_level_sites: dict # Dict[str, List[str]]

    _crawler_avaliable_tabs: list
    _crawler_open_tabs: cython.uint

    crawler_visited_urls: set # Set[str]
    crawler_blocked_domains: set # Set[str]
    crawler_valid_robots_domains: dict # Dict[str: Set[str]]

    crawler_website_data: dict

    crawler_depth: cython.uint
    
    _crawler_rotate_request: cython.bint
    _crawler_rotate_in_progress: cython.bint

    # Regex to find the domain of a URL. 
    # per example: https://desktop.github.com/test -> github.com
    crawler_domain_regex: re.Pattern
    crawler_robots_regex: re.Pattern

    Crawler_init: cython.bint
    Crawler_enter: cython.bint
    

    def __init__(self, sites:Dict[str, List[str]]={}, *args:tuple, **kwargs:dict):
        if(self.Crawler_init):
            return 
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Crawler")
        kwargs['verbose_depth'] = kwargs.get('verbose_depth', 0) + 1

        if(kwargs.pop("use_browser", True)):
            kwargs["use_pipeline"] = True

            super().__init__(*args, **kwargs)

        self.crawler_domain_regex = re.compile(r"^(https?://)?([^/]+\.)?([^/]+\.[^/]+).*")
        self.crawler_robots_regex = re.compile(r"disallowed(\W|\s)\s*((\w|\/)+)", re.IGNORECASE)

        self.crawler_sites = sites
        self.crawler_visited_urls = kwargs.pop("visited_urls", set())
        self.crawler_blocked_domains = kwargs.pop("blocked_domains", set(['reddit.com']))
        self.crawler_valid_robots_domains = dict()
        self.add_pipe("page", Crawler.get_urls, "Get all URLs (necessary for crawling)")

        self._crawler_avaliable_tabs = []
        self._crawler_open_tabs = 0

        self._crawler_rotate_request = False
        self._crawler_rotate_in_progress = False

        self.next_level_sites = dict()
        self.Crawler_init = True
        self.Crawler_enter = False

    async def __aenter__(self, *args, **kwargs):
        if(self.Crawler_enter):
            return
        self.Crawler_enter = True
        await super().__aenter__(self, *args, **kwargs)

        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await super().__aexit__(*args, **kwargs)
        self.Crawler_enter = False

    async def start_open_tabs(self, num_tabs:cython.uint, context:object) -> cython.void:
        self._crawler_avaliable_tabs.extend([await context.new_page() for _ in range(num_tabs)])
        self._crawler_open_tabs += num_tabs

    async def get_websites(self, max_tabs:cython.uint) -> list:
        # To be overridden when using a distributed crawler
        next_tabs:list = self._crawler_avaliable_tabs[:max_tabs]

        if(not len(next_tabs)):
            while(True):
                # Wait until at least one tab has finished
                await asyncio.sleep(1)

                if(len(self._crawler_avaliable_tabs)):
                    next_tabs[:max_tabs]
                    break

        self._crawler_avaliable_tabs = self._crawler_avaliable_tabs[len(next_tabs):]

        return next_tabs
            
    async def add_sites(self, sites:list):
        site:str
        for site in sites:
            match:object = self.crawler_domain_regex.search(site)
            if(match):
                domain:str = match.group(3)
                if(domain not in self.crawler_sites):
                    self.crawler_sites[domain] = {site}
                else:
                    self.crawler_sites.get(domain).add(site)

    async def _manage_website(self, tab:object, url:str, *, enforce_robots:cython.bint=False):
        try:
            loaded_site:object = await tab.goto(url, wait_until="networkidle")
                
            while(loaded_site is None):
                loaded_site = await tab.goto(url, wait_until="networkidle")
        except TimeoutError:
            print(f"[-] URL \"{url}\" Failed loading by timeout")
            self._crawler_avaliable_tabs.append(tab)
            return

        self._crawler_rotate_request = True

        loaded_site.domain = self.crawler_domain_regex.match(loaded_site.url).group(3)

        if(self._storage is not None):
            website_data = self._storage.storage_dict_cls()
        else:
            website_data = dict() 

        try:
            # In case of dynamically loaded websites
            for _ in asyncio.as_completed([page_alter(self, website_data, loaded_site) for page_alter in self._page_management]):
                await _
            for _ in asyncio.as_completed([data_alter(self, website_data, loaded_site) for data_alter in self._data_management]):
                await _

            if("urls" in website_data):
                site:str
                for site in website_data["urls"]:
                    if(site not in self.crawler_visited_urls):
                        self.crawler_visited_urls.add(site)

                        if(enforce_robots):
                            robots_rules: set = self.crawler_valid_robots_domains.get(domain)
                            if(robots_rules is None):
                                # Register robots.txt rules
                                robots_rules = self.check_robots(domain)

                            # https:// = 8 characters
                            site_path = site[site.find('/', 8):]
                            for rule in robots_rules:
                                if(site_path.startswith(rule)):
                                    # Blocked path
                                    continue

                        match:object = self.crawler_domain_regex.search(site)
                        if(match):
                            domain:str = match.group(3)
                            if(domain not in self.crawler_blocked_domains):
                                if(domain not in self.crawler_sites):
                                    self.next_level_sites[domain] = {site}
                                else:
                                    self.next_level_sites[domain].add(site)
            
            asyncio.create_task(self.add_data(loaded_site.domain, (loaded_site.url, website_data)))
        except Exception as e:
            print(f"Error on page {tab}: {e}")
        finally:
            self._crawler_avaliable_tabs.append(tab)

    async def get_crawling_urls(self, num_tabs:cython.uint) -> list:
        result:list = []
        end_domains:list = []
        n_domains:cython.uint = len(self.crawler_sites)
        added_websites:cython.uint
        _:cython.uint\

        domain_n:str
        domain_l:list
        added_websites:cython.uint
        for domain_n, domain_l in self.crawler_sites.items():
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
            self.crawler_sites.pop(domain)

        return result

    async def rotate_over_tabs(self, context, *, wait_done: bool=False):
        missing = [page for page in context.pages if page not in self._crawler_avaliable_tabs]
        rwait = np.random.uniform(0.3, 0.5, len(missing))

        for pwait, page in zip(rwait, missing):
            if(len(self._crawler_avaliable_tabs) == self._crawler_open_tabs):
                return
                
            await page.bring_to_front()
            await asyncio.sleep(pwait)

        self._crawler_rotate_in_progress = False

    async def crawl(self, contexts:list=[],
                        levels:cython.uint=0, 
                        *, 
                        num_contexts:cython.uint=1, 
                        max_tabs:cython.uint=25, 
                        close_contexts:cython.bint=False,
                        max_websites:cython.uint=-1,
                        enforce_robots:cython.bint=False
                        ) -> object:
        if(not contexts):
            _:cython.uint
            dyn_attr:dict = {}
            for _ in range(num_contexts):
                if(self.Rotating_proxies_init):
                    dyn_attr["proxy"] = {"server":self.new_proxy()}

                nc = await self.new_context(
                                            accept_downloads=False,
                                            **dyn_attr
                                        )

                contexts.append(nc)
                print("Added")
            close_contexts = True

        print("Start")
        context:object
        for context in contexts:
            for start_f in self._start_management:
                await start_f(self, context)
            
        print("End start")
        self.crawler_visited_urls.update(chain(*self.crawler_sites.values()))

        print("Context")
        tabs_per_context:cython.uint = ceil(max_tabs / num_contexts)
        for context in contexts:
            await self.start_open_tabs(tabs_per_context, context)

        tabs:list = []
        urls:list = []
        level:cython.uint
        if(max_websites == -1):
            max_websites = 999999
        
        searched_websites:cython.uint = 0
        for level in range(levels+1):
            print(f"\n\n# Level {level}:")

            self.crawler_depth = level

            while(len(self.crawler_sites)):
                if(searched_websites >= max_websites):
                    break
                print(f"  Found {len(self.crawler_visited_urls)} websites", end='\r')

                tabs = await self.get_websites(max_tabs)
                urls = await self.get_crawling_urls(len(tabs))
                searched_websites += len(urls)
                
                if(len(urls) != len(tabs)):
                    self._crawler_avaliable_tabs.extend(tabs[len(urls):])

                if(self._url_management):
                    altered_urls = set()
                    for alter_url in self._url_management:
                        altered_urls.update(await alter_url(self, urls))
                    
                    urls = altered_urls

                for tab, url in zip(tabs, urls):
                    asyncio.create_task(self._manage_website(tab, url, enforce_robots=enforce_robots))

                if(not self._crawler_rotate_in_progress and self._crawler_rotate_request):
                    self._crawler_rotate_in_progress = True
                    for context in contexts:
                        asyncio.create_task(self.rotate_over_tabs(context, wait_done=True))
                    
            # Wait until all tabs have finished
            # This is so that next_level_sites is complete
            #  otherwise, some sites may mix into the next depth level
            retries = 40
            while(len(self._crawler_avaliable_tabs) != self._crawler_open_tabs and retries):
                if(not self._crawler_rotate_in_progress and self._crawler_rotate_request):
                    self._crawler_rotate_in_progress = True
                    for context in contexts:
                        asyncio.create_task(self.rotate_over_tabs(context, wait_done=True))

                await asyncio.sleep(1)
                retries -= 1

            self.crawler_sites.clear()
            self.crawler_sites.update(self.next_level_sites)
            
            if(searched_websites >= max_websites):
                break

        print("\n\nCrawling completed")

        for context in contexts:
            print("Running end pipeline:", flush=True)
            for end_f in self._end_management:
                print(f" {end_f.__name__}")
                await end_f(self, context)

            if(close_contexts):
                await context.close()
        
        return contexts

    def check_robots(self, domain) -> set:
        rules_set: set
        with urlopen(f"https://{domain}/robots.txt") as stream:
            rules_set = set(self.crawler_robots_regex.findall(stream.read().decode("utf-8")))

        self.crawler_valid_robots_domains[domain] = rules_set
        return rules_set

    @staticmethod
    async def get_urls(self, data:dict, page:object):
        links:list = await page.frame.locator(":link:not(:visited)").evaluate_all("nodes => nodes.map(node => node.href)")
        if(links is not None):
            data["urls"] = set(links)

    @staticmethod
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
    async def get_videos(self, data:dict, page:object):
        videos:list = await page.frame.locator("video[src]").evaluate_all("nodes => nodes.map(node => node.src)")

        if(videos is not None):
            data["videos"] = set(videos)

    @staticmethod
    async def get_text(self, data:dict, page:object):
        text:str = await page.frame.inner_text('body')
        
        if(text is not None):
            data["text"] = text

    @staticmethod
    async def load_session(self, session_name:str, *args, **kwargs) -> None:
        await self.add_sites((site for session in (await super()._load_session(session_name)) for site in session))

    @staticmethod
    def block_resources(crawler:object):
        async def _block_resources(route:object):
            if(route.request.resource_type not in {"fetch", "script", "document"}):
                #print(f"Blocked resource: {route.request.resource_type}")
                await route.abort()
            else:
                await route.continue_()
        return _block_resources
