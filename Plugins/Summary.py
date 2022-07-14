# distutils: language=c++

import re

#from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BertTokenizerFast, EncoderDecoderModel
from pysummarization.nlpbase.auto_abstractor import AutoAbstractor
from pysummarization.tokenizabledoc.simple_tokenizer import SimpleTokenizer
from pysummarization.abstractabledoc.top_n_rank_abstractor import TopNRankAbstractor


from Core.Crawler import Crawler

#model = "google/pegasus-billsum"
#tokenizer = AutoTokenizer.from_pretrained(model)
#model = AutoModelForSeq2SeqLM.from_pretrained(model)
abstractor = AutoAbstractor()
abstractor.tokenizable_doc = SimpleTokenizer()
abstractor.delimiter_list = ['.', '\n']
abstract_d = TopNRankAbstractor()

whitespace_re = re.compile("[\n ]{2,}")

def mp_summary(data):
    data["summary"] = abstractor.summarize(whitespace_re.sub(' ', data["text"]), abstract_d)["summarize_result"]
    data["locks"] -= 1


async def summary(crawler:Crawler, data:dict, page:object):
    if("text" in data):
        with data._mutex:
            data["locks"] = data.get("locks", 0) + 1
        crawler.pool.apply_async(mp_summary, (data,))

def setup(crawler:Crawler):
    if(crawler.get_text not in crawler._page_management):
        crawler.add_pipe("page", crawler.get_text, "Text extractor")
    if(summary not in crawler._data_management):
        crawler.add_pipe("data", summary, "Website summaries")
