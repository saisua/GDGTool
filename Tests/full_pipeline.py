# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler
import re
from datetime import datetime

format = re.compile("\?.*")

start_time = None
async def start(obj:Crawler, window:object):
    global start_time
    start_time = datetime.now()

async def format_urls(obj:Crawler, urls:set) -> list:
    return {format.sub("", url) for url in urls}

async def get_images(obj:Crawler, data:dict, page:object):
    data["imgs"] = await page.frame.locator(":visible img[src]").evaluate_all("nodes => nodes.map(node => node.src)")

async def count_images(obj:Crawler, data:dict, page:object):
    print(f"Website {page.url} contains {len(data['imgs'])} images!")

async def end(obj:Crawler, window:object):
    global start_time
    print(f"Crawling time: {datetime.now() - start_time}")


def on_request(crawler:Crawler):
    crawler.data["Requests"] = []
    async def _on_request(request:object):
        crawler.data["Requests"].append(request.url)
    
    return _on_request

def route_response(crawler:Crawler):
    async def _route_response(route):
        if(route.request.resource_type not in {"fetch", "script", "document"}):
            print(f"Blocked resource: {route.request.resource_type}")
            await route.abort()
        else:
            await route.continue_()
    return _route_response

async def full_pipeline():
    sites = {
        "github.com": ["https://github.com?test=BAD", ],
        "playwright.dev": ["https://playwright.dev", ],
    }

    crawler = Crawler(sites, remove_old_data=True)

    crawler.add_pipe("event", ("request", on_request))
    crawler.add_pipe("routing", ("**", route_response))

    crawler.add_pipe("start", start, "Start time")
    crawler.add_pipe("url", format_urls, "Format URL")
    crawler.add_pipe("page", get_images, "Get images")
    crawler.add_pipe("data", count_images, "Count images")
    crawler.add_pipe("end", end, "End time")

    async with crawler as cr:
        await cr.crawl()

if(__name__ == "__main__"):
    asyncio.run(full_pipeline())