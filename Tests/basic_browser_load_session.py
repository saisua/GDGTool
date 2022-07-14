# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Browser import Browser

async def open_browser_test():
    async with Browser(remove_old_data=True) as br:
        await br.load_session("session.0", load_wait=True)

if(__name__ == "__main__"):
    asyncio.run(open_browser_test())