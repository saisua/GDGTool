# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import cython
from datetime import datetime

import numba

from Core.Crawler import Crawler

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

async def full_pipeline():
    sites = {
        "duckduckgo.com": ["https://duckduckgo.com/?t=ffab&q=scraping+test&atb=v320-1&ia=web", ],
    }

    # Chromium (50 tabs) : 746 in 18.05
    # 
    crawler = Crawler(sites, remove_old_data=True, use_resources=False, use_session=False, headless=True)

    crawler.add_pipe("routing", ("**/*", route_response))

    await crawler.open()
    start_time = datetime.now()
    await crawler.crawl(levels=1, max_tabs=50, num_contexts=5)
    print(f"Crawling time: {datetime.now() - start_time}")
    print(f"Got {len(crawler.visited_urls)} URLs")
    await crawler.close()

if(__name__ == "__main__"):
    asyncio.run(full_pipeline())