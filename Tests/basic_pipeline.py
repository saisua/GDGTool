# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler
import re

format = re.compile("\?.*")

async def format_urls(urls:set) -> list:
    return {format.sub("", url) for url in urls}

async def basic_pipeline():
    sites = {
        "github.com": ["https://github.com?test=BAD", ],
        "playwright.dev": ["https://playwright.dev", ],
    }

    crawler = Crawler(sites, remove_old_data=True)

    crawler.add_pipe("url", format_urls, "Format URL")

    async with crawler as cr:
        await cr.crawl()

if(__name__ == "__main__"):
    asyncio.run(basic_pipeline())