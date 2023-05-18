
from Core.Crawler import Crawler
from EndScripts.Summary import main

async def summarize(crawler:Crawler):
    main(folder=crawler.storage_path)

def setup(crawler:Crawler):
	if(crawler._pipeline is not None):
		if(crawler.text_extraction not in crawler._page_management):
			crawler.add_pipe("page", crawler.text_extraction, "Text extractor")
		if(summarize not in crawler._post_management):
			crawler.add_pipe("post", summarize, "Full search information graph")
		
		return True
	return False
