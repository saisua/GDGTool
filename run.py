import asyncio

#from Tests.basic_open_browser import open_browser_test as test
#from Tests.basic_crawl_websites import basic_crawl_websites as test
#from Tests.basic_pipeline import basic_pipeline as test
from Tests.full_pipeline import full_pipeline as test

def main():
    asyncio.run(test())

if(__name__ == "__main__"):
    main()