# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler

from Plugins.Summary import setup as summary_setup

async def basic_search():
    query = "Red dead redemption videogame"

    async with Crawler(storage_name=f"{query} search", remove_old_data=True, headless=False) as cr:
        await cr.search(query)
        summary_setup(cr)
        
        await cr.crawl(levels=1, max_tabs=5, max_websites=20)

if(__name__ == "__main__"):
    asyncio.run(basic_search())