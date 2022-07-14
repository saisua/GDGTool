# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Browser import Browser

async def open_browser_test():
    async with Browser(remove_old_data=True, headless=False) as br:
        context = await br.browser.new_context()

        sites = ["https://github.com", "https://playwright.dev", "https://youtube.com",
                "https://google.com", "https://facebook.com", "https://twitter.com",
                "https://instagram.com", "https://linkedin.com", "https://pinterest.com",
                "https://reddit.com", "https://quora.com", "https://stackoverflow.com",
                "https://medium.com", "https://hola.com", "https://wikipedia.org"]
        sites = ["https://duckduckgo.com"]
        async for _ in br.open_websites(context, sites):
            print(await _)

        while(not br.closed):
            await asyncio.sleep(3)

        
        await context.close()

if(__name__ == "__main__"):
    asyncio.run(open_browser_test())