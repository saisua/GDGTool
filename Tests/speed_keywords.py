# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import cython
from datetime import datetime

from Core.Crawler import Crawler
from Plugins.Keywords import setup

def route_response(crawler:Crawler):
	@cython.cdivision(True)
	@cython.boundscheck(False)
	@cython.wraparound(False)
	@cython.cfunc
	async def _route_response(route):
		if(route.request.resource_type in {"image", "media", "font"}):
			#print(f"Blocked resource: {route.request.resource_type}")
			await route.abort()
		else:
			await route.continue_()
	return _route_response

async def speed_pipeline():
	sites = {
        "crawler-test.com": ["https://crawler-test.com/", ],
	}

	# Chromium (50 tabs) : 746 in 18.05
	# 
	init_time = datetime.now()
	crawler = Crawler(sites, 
		   install_addons=False, 
		   browser_name="firefox",
		   storage_path=os.environ.get("HOME", '.'),
		   storage_name='SpeedTest', 
		   remove_old_data=True, 
		   use_resources=False, 
		   use_session=False, 
		   headless=True
	)
	setup(crawler)

	crawler.add_pipe("routing", ("**/*", route_response))

	await crawler.open()
	start_time = datetime.now()
	await crawler.crawl(levels=1, max_tabs=10, max_websites=250)
	end_time = datetime.now()
	
	print(f"\nTotal time: {end_time - init_time}\nInitialization time: {start_time - init_time}\nCrawling time: {end_time - start_time}")
	print(f"Got {len(crawler.crawler_visited_urls)} URLs")
	await crawler.close()

if(__name__ == "__main__"):
	#with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
	asyncio.run(speed_pipeline())