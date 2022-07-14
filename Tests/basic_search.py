# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler

async def basic_search():
    query = "Alquiler pisos en Valencia"

    async with Crawler(remove_old_data=True) as cr:
        await cr.search(query)
        await cr.crawl(levels=1)

if(__name__ == "__main__"):
    asyncio.run(basic_search())