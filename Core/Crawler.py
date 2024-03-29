# distutils: language=c++

import asyncio
import threading
import traceback
import re
import cython
from typing import *
from itertools import chain
from math import ceil
import numpy as np

from urllib.request import urlopen

from playwright.async_api import TimeoutError, Error as NotAttachedToDomError, BrowserContext, Locator

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

	_level_barrier: threading.Barrier

	# Regex to find the domain of a URL. 
	# per example: https://desktop.github.com/test -> github.com
	crawler_domain_regex: re.Pattern
	crawler_robots_regex: re.Pattern

	Crawler_init: cython.bint
	Crawler_enter: cython.bint

	storage_function: Callable
	

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

		self._crawler_avaliable_tabs = []
		self._crawler_open_tabs = 0

		self._crawler_rotate_request = False
		self._crawler_rotate_in_progress = False

		self.next_level_sites = dict()
		self.Crawler_init = True
		self.Crawler_enter = False

		if(self._storage is not None):
			self.storage_function = self._storage.storage_dict_cls
		else:
			self.storage_function = dict() 

		self._level_barrier = None

	async def __aenter__(self, *args, step:cython.bint=0, **kwargs):
		if(self.Crawler_enter): return
		if(step != 0): return

		self.Crawler_enter = True
		await super().__aenter__(*args, **kwargs)

		return self

	async def __aexit__(self, *args, step:cython.bint=1, **kwargs) -> None:
		if(not self.Crawler_enter): return
		if(step != 1): return

		await super().__aexit__(*args, **kwargs)
		self.Crawler_enter = False

	async def start_open_tabs(self, num_tabs:cython.uint, context:object) -> cython.void:
		self._crawler_avaliable_tabs.extend([await context.new_page() for _ in range(num_tabs)])
		self._crawler_open_tabs += num_tabs

	async def get_tabs(self, max_tabs:cython.uint) -> list:
		# To be overridden when using a distributed crawler
		next_tabs:list = self._crawler_avaliable_tabs[:max_tabs]

		if(not len(next_tabs)):
			while(True):
				# Wait until at least one tab has finished
				await asyncio.sleep(1)

				if(len(self._crawler_avaliable_tabs)):
					next_tabs[:max_tabs]
					break
				# print("Waiting for available tabs")

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

	async def _perform_data_management(self, website_data, tab, loaded_site):
		await asyncio.gather(*(
			data_alter(self, website_data, tab) 
			for data_alter in self._data_management
		))

		self._crawler_avaliable_tabs.append(tab)

		try:
			await self._level_barrier.wait(15)
		except threading.BrokenBarrierError:
			pass

	async def _manage_website(self, 
			   tab:object, 
			   url:str, *, 
			   enforce_robots:cython.bint=False,
			   do_data_management:cython.bint=False,
			   analize_new_urls:cython.bint=True):
		try:
			loaded_site:object = await tab.goto(url, wait_until="networkidle")
				
			if(not loaded_site):
				for _ in range(5):
					loaded_site = await tab.goto(url, wait_until="networkidle")
					if(loaded_site):
						break
				else:
					return
		except TimeoutError:
			print(f"[-] URL \"{url}\" Failed loading by timeout")

			self._crawler_avaliable_tabs.append(tab)
			return
		except Exception:
			return

		self._crawler_rotate_request = True

		loaded_site.domain = self.crawler_domain_regex.match(loaded_site.url).group(3)

		website_data = self.storage_function()

		added_tab: cython.bint = False
		try:
			# In case of dynamically loaded websites
			await asyncio.gather(*(
				page_alter(self, website_data, tab) 
				for page_alter in self._page_management
			))
			
			if(do_data_management):
				await asyncio.to_thread(
						self._perform_data_management(website_data, tab, loaded_site)
				)
			else:
				self._crawler_avaliable_tabs.append(tab)
				added_tab = True

			if(analize_new_urls and "urls" in website_data):
				# This also stores the data
				await self._analize_new_urls(website_data, enforce_robots)

			self._storage.add_data(loaded_site.domain, (loaded_site.url, website_data))

		except Exception as e:
			print(f"Error on page {tab}: {e}")

			if(not added_tab):
				self._crawler_avaliable_tabs.append(tab)

			print(traceback.format_exc())

	async def _analize_new_urls(self, website_data: dict, enforce_robots: cython.bint):
		site: str
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

				match: object = self.crawler_domain_regex.search(site)
				if(match):
					domain: str = match.group(3)
					if(domain not in self.crawler_blocked_domains):
						if(domain not in self.crawler_sites):
							self.next_level_sites[domain] = {site}
						else:
							self.next_level_sites[domain].add(site)

	def get_crawling_urls(self, num_tabs:cython.uint) -> list:
		result:list = []
		end_domains:list = []
		n_domains:cython.uint = len(self.crawler_sites)
		added_websites:cython.uint
		_:cython.uint

		domain_n:str
		domain_l:list
		added_websites:cython.uint
		# Cyclically add urls. If the domain is left empty, remove it
		for domain_n, domain_l in self.crawler_sites.items():
			added_websites = ((num_tabs - len(result)) // n_domains) or 1
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

	async def crawl(self, contexts:List[BrowserContext]=[],
						levels:cython.uint=0, 
						*, 
						num_contexts:cython.uint=1, 
						max_tabs:cython.uint=25, 
						close_contexts:cython.bint=False,
						max_websites:cython.uint=-1,
						enforce_robots:cython.bint=False
						) -> object:
		if(Crawler.url_extraction not in self._page_management):
			self.add_pipe("page", Crawler.url_extraction, "Get all URLs (necessary for crawling)")

		context: BrowserContext
		if(not contexts):
			dyn_attr:dict = {}
			if(self.Rotating_proxies_init):
				dyn_attr["proxy"] = {"server":self.new_proxy()}

			context = await self._new_context(
										accept_downloads=False,
										**dyn_attr
									)

			close_contexts = True
		else: 
			context = contexts[0]

		start_f: Callable
		for start_f in self._start_management:
			await start_f(self, context)
			
		#print("End start")
		self.crawler_visited_urls.update(chain(*self.crawler_sites.values()))

		#print("Context")
		await self.start_open_tabs(max_tabs, context)

		tabs:list = []
		urls:list = []
		level:cython.uint
		if(max_websites == -1):
			max_websites = 999999
		
		searched_websites:cython.uint = 0
		for level in range(levels+1):
			print(f"\n\n# Level {level}:\n  To search: {len(self.crawler_sites)} domains", flush=False)

			self.crawler_depth = level

			while(len(self.crawler_sites)):
				if(searched_websites >= max_websites):
					break
				# print(f"  Found {len(self.crawler_visited_urls)} websites", end='\r')

				tabs = await self.get_tabs(max_tabs)
				urls = self.get_crawling_urls(len(tabs))
				searched_websites += len(urls)
				
				if(self._url_management):
					urls = set(
						await asyncio.gather(
							*(
								alter_url(self, urls)
								for alter_url in self._url_management
							)
						)
					)

				if(len(urls) != len(tabs)):
					self._crawler_avaliable_tabs.extend(tabs[len(urls):])

				has_data_management: cython.bint = len(self._data_management)

				if(has_data_management):
					self._level_barrier = threading.Barrier(len(urls) + 1, timeout=20)

				is_last_level = level == levels
				for tab, url in zip(tabs, urls):
					asyncio.create_task(
						self._manage_website(
							tab,
							url,
							enforce_robots=enforce_robots,
							do_data_management=has_data_management,
							analize_new_urls=not is_last_level,
					))

				if(not self._crawler_rotate_in_progress and self._crawler_rotate_request):
					self._crawler_rotate_in_progress = True
					asyncio.create_task(self.rotate_over_tabs(context, wait_done=True))
					

			if(has_data_management):
				for _ in range(15):
					try:
						await self._level_barrier.wait(1)
						break
					except threading.BrokenBarrierError:
						await asyncio.sleep(1)
						if(not self._crawler_rotate_in_progress and self._crawler_rotate_request):
							self._crawler_rotate_in_progress = True
							asyncio.create_task(self.rotate_over_tabs(context, wait_done=True))

			for _ in range(20):
				if(len(self._crawler_avaliable_tabs) == self._crawler_open_tabs):
					break
				await asyncio.sleep(0.5)

			self.crawler_sites.clear()
			self.crawler_sites.update(self.next_level_sites)
			
			if(searched_websites >= max_websites):
				break
		
		for _ in range(200):
			if(len(self._crawler_avaliable_tabs) == self._crawler_open_tabs):
				break
			await asyncio.sleep(0.5)

		print("\n\nCrawling completed")

		# print("Running end pipeline:", flush=True)
		for end_f in self._end_management:
			print(f" {end_f.__name__}")
			await end_f(self, context)

		if(close_contexts):
			await context.close()
		
		return [context]

	def check_robots(self, domain) -> set:
		rules_set: set
		with urlopen(f"https://{domain}/robots.txt") as stream:
			rules_set = set(self.crawler_robots_regex.findall(stream.read().decode("utf-8")))

		self.crawler_valid_robots_domains[domain] = rules_set
		return rules_set


	async def get_urls(self, page:object) -> list:
		return await page.frames[0].locator(":link:not(:visited)").evaluate_all("nodes => nodes.map(node => node.href)")

	@staticmethod
	async def url_extraction(self, data:dict, page:object):
		links_locator: Locator = page.locator(':link:visible')

		link_set: set = set()
		current_links: Union[None, List[str]] = await links_locator.evaluate_all("nodes => nodes.map(node => node.href)")
		if(current_links is not None):
			link_set.update(current_links)

		last_found_links: cython.uint = 0
		found_links: cython.uint = await links_locator.count()
		for _ in range(10):
			try:
				await links_locator.last.scroll_into_view_if_needed(timeout=1_000)
			except (TimeoutError, NotAttachedToDomError):
				pass

			links_locator = page.locator(':link:visible')

			found_links = await links_locator.count()
			if(found_links != last_found_links):
				last_found_links = found_links
			elif(last_found_links):
				break
			
			current_links = await links_locator.evaluate_all("nodes => nodes.map(node => node.href)")
			if(current_links is not None):
				link_set.update(current_links)

			await asyncio.sleep(0.5)
		else:
			return

		current_links = await page.locator(':link:visible').evaluate_all("nodes => nodes.map(node => node.href)")
		if(current_links is not None):
			link_set.update(current_links)

		data['urls'] = link_set
		
	async def get_images(self, page:object) -> set:
		images:list = await page.frames[0].locator("img[src]").evaluate_all("nodes => nodes.map(node => node.src)")
		while(not images):
			await asyncio.sleep(0.5)
			images = await page.frames[0].locator("img[src]").evaluate_all("nodes => nodes.map(node => node.src)")

			if(images is None):
				return 

		if(images is not None):
			return set(images)

	async def image_extraction(self, data:dict, page:object):
		images:list = await page.frames[0].locator("img[src]").evaluate_all("nodes => nodes.map(node => node.src)")
		while(not images):
			await asyncio.sleep(0.5)
			images = await page.frames[0].locator("img[src]").evaluate_all("nodes => nodes.map(node => node.src)")

			if(images is None):
				return 

		if(images is not None):
			data["images"] = set(images)

	async def video_extraction(self, data:dict, page:object):
		videos:list = await page.frames[0].locator("video[src]").evaluate_all("nodes => nodes.map(node => node.src)")

		if(videos is not None):
			data["videos"] = set(videos)

	async def get_text(self, page:object) -> str:
		text_locator: Locator = page.locator('body')
		
		text: str
		for _ in range(10):
			text = await text_locator.inner_text()
			if(text):
				return text

	@staticmethod
	async def text_extraction(self, data:dict, page:object):
		text_locator: Locator = page.locator('body')
		
		text: str
		for _ in range(10):
			text = await text_locator.inner_text()
			if(text):
				data["text"] = text
				return

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
