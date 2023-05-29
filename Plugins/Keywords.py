
from Core.Crawler import Crawler
from EndScripts.Keywords import main

async def get_keywords(crawler:Crawler):
    main(folder=crawler.storage_path, storage_base_path=crawler.storage_base_path)

def setup(crawler:Crawler) -> bool:
	if(crawler._pipeline is not None):
		if(crawler.text_extraction not in crawler._pipeline._page_management):
			crawler._pipeline.add_pipe("page", crawler.text_extraction, "Text extractor")
		if(get_keywords not in crawler._pipeline._post_management):
			crawler._pipeline.add_pipe("post", get_keywords, "Generate most important keywords")

		return True
	return False
