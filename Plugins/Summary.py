# distutils: language=c++

import re
import os
import cython

#from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BertTokenizerFast, EncoderDecoderMode   l
#from pysummarization.nlpbase.auto_abstractor import AutoAbstractor
#from pysummarization.tokenizabledoc.simple_tokenizer import SimpleTokenizer
#from pysummarization.abstractabledoc.top_n_rank_abstractor import TopNRankAbstractor
#from pysummarization.similarityfilter.jaccard import Jaccard

from transformers import pipeline
from gensim.summarization.summarizer import summarize

model_name = "facebook/bart-large-cnn" # "t5-base"
model_max_input_tokens = 1024
summarizer = pipeline('summarization', model=model_name, tokenizer=model_name, framework="tf")


from Core.Crawler import Crawler

#model = "google/pegasus-billsum"
#tokenizer = AutoTokenizer.from_pretrained(model)
#model = AutoModelForSeq2SeqLM.from_pretrained(model)
#abstractor = AutoAbstractor()
#abstractor.tokenizable_doc = SimpleTokenizer()
#abstractor.delimiter_list = ['.', '\n']
#abstract_d = TopNRankAbstractor()

whitespace_re = re.compile("\s\s+")

@cython.cfunc
def mp_summary(data):
    data["summary"] = summarizer(
        summarize(
            whitespace_re.sub(
                ' ',
                data["text"]
            ),
            word_count=model_max_input_tokens
        ),
        min_length=30
    )[0][0]["summary_text"]
    #data["summary"] = abstractor.summarize(whitespace_re.sub(' ', data["text"]), abstract_d)["summarize_result"]
    data["locks"] -= 1 


@cython.cfunc
async def summary(crawler:Crawler, data:dict, page:object):
    if("text" in data):
        with data._mutex:
            data["locks"] = data.get("locks", 0) + 1
        crawler.pool.apply_async(mp_summary, (data,))
        
@cython.cfunc
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
            all_files.append(website)
            summary = data.get('text', '')

            if(type(summary) != str):
                summary = '\n'.join(summary)
            full_data.append(summary)

    await crawler.add_data("Full_summary", ("from_websites", all_files))
    await crawler.add_data("Full_summary", ("full_data", '\n'.join(full_data)))
    await crawler.add_data("Full_summary", ("full_summary", 
        summarizer(
            summarize(
                whitespace_re.sub(
                    ' ',
                    data["text"]
                ),
                word_count=model_max_input_tokens
            ),
            min_length=30
        )[0][0]["summary_text"]
    ))

def setup(crawler:Crawler):
    if(crawler.get_text not in crawler._page_management):
        crawler.add_pipe("page", crawler.get_text, "Text extractor")
    if(summary not in crawler._data_management):
        crawler.add_pipe("data", summary, "Website summaries")
    if(full_summary not in crawler._post_management):
        crawler.add_pipe("post", full_summary, "Full search summary")
