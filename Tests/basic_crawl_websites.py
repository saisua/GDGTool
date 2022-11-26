# distutils: language=c++

import asyncio
from email.base64mime import header_length
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler

async def basic_crawl_websites():
    sites = {
        "duckduckgo.com": ["https://duckduckgo.com/?t=ffab&q=scraping+test&atb=v320-1&ia=web", ],
    }

    async with Crawler(sites, remove_old_data=True, use_resources=False, use_session=False, headless=False) as cr:
        await cr.crawl(levels=0, max_tabs=20, num_contexts=1)

if(__name__ == "__main__"):
    asyncio.run(basic_crawl_websites())