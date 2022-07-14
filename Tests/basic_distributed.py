# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Distributed import Distributed, Controller

async def distributed_test():
    sites = {
        "github.com": ["https://github.com", ],
        "playwright.dev": ["https://playwright.dev", ],
    }
    
    async with Controller(sites, remove_old_data=True) as dcr:
        #dcr.cluster.discover_nodes(["127.0.0.1:970"])
        dcr.cluster.print_status()
        job = dcr.cluster.submit(3)
        dcr.cluster.wait()
        print(job.result)

if(__name__ == "__main__"):
    asyncio.run(distributed_test())