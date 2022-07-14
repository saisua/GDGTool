# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler
from Plugins.Image_analizer import setup

def block_resources(crawler:object):
        async def _block_resources(route:object):
            if(route.request.resource_type not in {"fetch", "script", "document", "image"}):
                #print(f"Blocked resource: {route.request.resource_type}")
                await route.abort()
            else:
                await route.continue_()
        return _block_resources

async def basic_crawl_websites():
    crawler = Crawler(remove_old_data=True, headless=False, processes=2)
    setup(crawler)
    
    #crawler.add_pipe("routing",  ("**", block_resources), "Block resources")
    await crawler.search_images("armadillo")

    async with crawler as cr:
        await cr.crawl(levels=0)

if(__name__ == "__main__"):
    asyncio.run(basic_crawl_websites())