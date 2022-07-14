# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler
from Plugins.Summary import setup

async def basic_crawl_websites():
    # Resources must be True
    crawler = Crawler(remove_old_data=True, headless=False)
    setup(crawler)
    crawler.add_pipe("routing",  ("**", Crawler.block_resources), "Block resources")
    await crawler.search_general("Aragorn")

    async with crawler as cr:
        await cr.crawl(levels=1, num_contexts=1, max_tabs=25)

if(__name__ == "__main__"):
    asyncio.run(basic_crawl_websites())