# distutils: language=c++

import cython
import asyncio
from sys import stdin
from API.Live import Live_browser

HOME = 'https://duckduckgo.com'

block_new_pages: bool = True
async def manage_new_page(page):
    print("New page")

    global block_new_pages
    if(block_new_pages):
        await page.close()

async def manage_contexts(contexts):
    print("Setting up contexts...")
    for context in contexts:
        context.on("page", manage_new_page)
    print("Contexts set up")

async def manage_page_routed(browser, page):
    print("Routed page")

async def manage_new_page_routed(browser, page):
    global block_new_pages
    print("Routed new page")
    if(not block_new_pages and page == page.context.pages[-1]):
        async for _ in browser.open_websites(page.context, {HOME}, override=False):
            await _
        await page.bring_to_front()


async def main():
    global block_new_pages
    br: object
    i: str

    with Live_browser(
                remove_old_data=True,
                headless=False,
                browser_name="firefox",
                browser_persistent=False,
                verbose=True,
                install_addons="search",
            ) as br:
        br.open_websites(websites=[HOME], run_mode="agen")
        br.print_state()

        br.apply_contexts(manage_contexts, run_mode="async")
        br.url_tracking(manage_page_routed, manage_new_page_routed)
        # br.search("test")

        br.print_state()

        try:
            while True:
                await asyncio.sleep(3)
                continue
            
                i = input("> ") 

                if(i == "exit"):
                    break
                elif(i == "wait"):
                    await asyncio.sleep(3)
                elif(i == "block"):
                    block_new_pages = not block_new_pages
                elif(i):
                    try:
                        exec(i)
                    except KeyboardInterrupt:
                        break
                    except Exception as err:
                        print(err)
        except KeyboardInterrupt:
            pass

if(__name__ == "__main__"):
    asyncio.run(main())
