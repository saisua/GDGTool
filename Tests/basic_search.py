# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler


async def basic_search():
    query = "Aragorn the lord of the rings"

    async with Crawler(storage_name=f"{query} search", remove_old_data=True, headless=False) as cr:
        await cr.search(query)
        cr.add_pipe("page", cr.get_text, "Text extractor")
        cr.add_pipe("post", full_summary, "Full summary")
        await cr.crawl(levels=1, max_tabs=5, max_websites=20)

if(__name__ == "__main__"):
    asyncio.run(basic_search())