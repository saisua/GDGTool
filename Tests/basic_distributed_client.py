import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Distributed import Client

async def basic_distributed_client():
    async with Client() as cl:
        cl.sites.update({"duckduckgo.com":["https://duckduckgo.com/?t=ffab&q=scraping+test&atb=v320-1&ia=web"]})
        
        await cl.delegate("crawl", levels=1, num_contexts=1)
        #await cl.run_async("crawl", levels=1, num_contexts=1)

if(__name__ == "__main__"):
    try:
        asyncio.run(basic_distributed_client())
    except ValueError:
        pass