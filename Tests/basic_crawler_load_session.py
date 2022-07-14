# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler

async def open_browser_test():
    async with Crawler(remove_old_data=True) as cr:
        await cr.load_session("session.0")

        await cr.crawl()

if(__name__ == "__main__"):
    asyncio.run(open_browser_test())