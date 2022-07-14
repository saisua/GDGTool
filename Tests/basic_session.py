# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Browser import Browser

async def open_browser_test():
    async with Browser(remove_old_data=True, autosave_session=True) as br:
        window = await br.browser.new_context()

        sites = ["https://github.com", "https://playwright.dev", "https://twitter.com",
                "https://linkedin.com", "https://pinterest.com",
                "https://reddit.com", "https://quora.com"]
        async for _ in br.open_websites(window, sites):
            print(await _)

if(__name__ == "__main__"):
    asyncio.run(open_browser_test())