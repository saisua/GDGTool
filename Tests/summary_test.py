# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler
from EndScripts.Summary import setup

async def basic_summarization():
    search = "Cork material"
    # Resources must be True
    crawler = Crawler(storage_name=f"{search} summarization", remove_old_data=True, headless=False)
    setup(crawler)
    crawler.add_pipe("routing",  ("**", Crawler.block_resources), "Block resources")
    await crawler.search_general(search)

    async with crawler as cr:
        await cr.crawl(levels=1, num_contexts=1, max_tabs=5, max_websites=30)

if(__name__ == "__main__"):
    asyncio.run(basic_summarization())