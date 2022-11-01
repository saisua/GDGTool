# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler

async def full_summary(crawler:Crawler, context):
    all_files = []
    full_data = []

    path:str
    dirs:list
    files:list
    for path, dirs, files in os.walk(crawler.storage_path):
        for file in files:
            all_files.append(file)

    domain:str
    pending_data:list
    website:str
    data:dict
    for domain, pending_data in crawler.storage_data.items():
        for website, data in pending_data:
            print(data)
            all_files.append(website)
            summary = data.get('text', '')

            if(type(summary) != str):
                summary = '\n'.join(summary)
            full_data.append(summary)

    await crawler.add_data("Full_summary", ("from_websites", {'urls': all_files}))
    await crawler.add_data("Full_summary", ("full_data", {'full_data':'\n'.join(full_data)}))

async def basic_search():
    query = "Aragorn the lord of the rings"

    async with Crawler(storage_name=f"{query} search", remove_old_data=True) as cr:
        await cr.search(query)
        cr.add_pipe("page", cr.get_text, "Text extractor")
        cr.add_pipe("end", full_summary, "Full summary")
        await cr.crawl(levels=1, max_tabs=5, max_websites=15)

if(__name__ == "__main__"):
    asyncio.run(basic_search())