# distutils: language=c++

import re
import os
import cython

#from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BertTokenizerFast, EncoderDecoderMode   l
#from pysummarization.nlpbase.auto_abstractor import AutoAbstractor
#from pysummarization.tokenizabledoc.simple_tokenizer import SimpleTokenizer
#from pysummarization.abstractabledoc.top_n_rank_abstractor import TopNRankAbstractor
#from pysummarization.similarityfilter.jaccard import Jaccard

import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')


import spacy
nlp = spacy.load("en_core_web_md")

from Core.Crawler import Crawler

@cython.cfunc
def mp_summary(data):
    #data["summary"] = 
    data["locks"] -= 1 


async def summary(crawler:Crawler, data:dict, page:object):
    if("text" in data):
        with data._mutex:
            data["locks"] = data.get("locks", 0) + 1
        crawler.resources_pool.apply_async(mp_summary, (data,))
        
async def full_summary(crawler:Crawler):
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
            all_files.append(website)
            summary = data.get('text', '')

            if(type(summary) != str):
                summary = '\n'.join(summary)
            full_data.append(summary)

    await crawler.add_data("Full_summary", ("from_websites", all_files))
    await crawler.add_data("Full_summary", ("full_data", '\n'.join(full_data)))
    await crawler.add_data("Full_summary", ("full_summary", ''
    ))

def setup(crawler:Crawler):
    if(crawler.get_text not in crawler._page_management):
        crawler.add_pipe("page", crawler.get_text, "Text extractor")
    if(summary not in crawler._data_management):
        crawler.add_pipe("data", summary, "Website summaries")
    if(full_summary not in crawler._post_management):
        crawler.add_pipe("post", full_summary, "Full search summary")
