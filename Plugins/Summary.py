# distutils: language=c++

from Core.Crawler import Crawler

import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')

#export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
import spacy, coreferee
nlp = spacy.load("en_core_web_md")
nlp.add_pipe('coreferee')

import gensim
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from nltk.stem import WordNetLemmatizer, SnowballStemmer
from nltk.stem.porter import *
from nltk.corpus import wordnet

import numpy as np
import multiprocessing as mp

import wikipedia

import cython

from sortedcontainers import SortedList

from itertools import chain
import os

from Plugins.utils.coref_resolution import solve as solve_coref

stemmer = SnowballStemmer('english')
lemmatizer = WordNetLemmatizer()
@cython.cfunc
def lemmatize_stemming(text: str):
    return stemmer.stem(lemmatizer.lemmatize(text, pos='v'))

@cython.cfunc
def preprocess(text: str) -> list:
    result: list = []
    for token in simple_preprocess(text):
        if(token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3):
            result.append(token)
    return result

preprocess("There was a little girl called Thais that was so beautiful")

@cython.cfunc
def simy(word: str, query):
    return query.similarity(nlp(word))
def get0(l): return l[0]

allowed_ents = {
  "PERSON",
  "LOC"
}

@cython.cfunc
def spacy_most_similar(word: str, topn: cython.uint =10):
  ms = nlp.vocab.vectors.most_similar(
      nlp(word).vector.reshape(1,nlp(word).vector.shape[0]),
      n=topn
  )
  words = [nlp.vocab.strings[w] for w in ms[0][0]]
  distances = ms[2]
  return words, distances

def get_important_words(queries, 
                       *, 
                       get_top_words: int=15,
                       similar_word_variations: int=2):
    result = set()
    for query in queries:
        queryd = nlp(query)

        summary = wikipedia.summary(query)
        summary_ents = {str(ent) for ent in nlp(summary).ents if ent.label_ in allowed_ents}
        preprocessed = preprocess(summary)

        sorted_words = SortedList([(simy(word, queryd), word) for word in preprocessed if word not in spacy.lang.en.stop_words.STOP_WORDS], key=get0)

        for word in preprocessed:
            sorted_words.add((simy(word, queryd), word))

        query_words = set(query.split())

        top_words = {w[1] for w in sorted_words[-get_top_words:]}
        top_words -= query_words
        top_words -= summary_ents

        sims = [spacy_most_similar(query), *(
            spacy_most_similar(f"{query} {word}", topn=similar_word_variations)
                for word in top_words
        )]

        full_words = set(chain(*(s[0][:get_top_words] for s in sims)))
        full_words |= query_words
        full_words |= summary_ents
        full_words.add(query)

        result.update(full_words)
    return result

@cython.cfunc
def join_sents(s1: str, s2: str):
    return f"{s1}. {s2}"


sre = re.compile('\s+')
@cython.cfunc
def summarize_by_keywords(text: str, keywords: list, *, sentences: int=10):
    # TODO: coreference resolution that does not need lots of ram
    text_doc = nlp(solve_coref(nlp(text)))
    full_words_docs = [nlp(w) for w in keywords]

    sentences_list = []
    sents_index_range = []
    for sentence in text_doc.sents:
        similarities = []
        sentences_list.append(similarities)
        for word_doc in full_words_docs:
            similarities.append(sentence.similarity(word_doc))

    sentences_list = np.array(sentences_list)
    filter_stats = np.max(sentences_list, axis=1) * np.mean(sentences_list, axis=1)
    fsort_stats = np.argsort(filter_stats)

    sents_index_range = np.arange(len(sentences_list))[fsort_stats][-sentences:]

    filtered_sentences = []
    sentences_remaining = set(sents_index_range)
    for sent_index, sentence in enumerate(text_doc.sents):
        if sent_index in sentences_remaining:
            filtered_sentences.append(sentence)
            sentences_remaining.remove(sent_index)
            if not len(sentences_remaining):
                break

    sents = []
    current_sent = str(filtered_sentences[0])
    current_index = sents_index_range[0]
    for ns, ni in zip(filtered_sentences[1:], sents_index_range[1:]):
        if(ni != current_index + 1):
            try:
                current_sent = join_sents(current_sent, ns)
            except RuntimeError:
                sents.append(current_sent)
                current_sent = str(ns)  
        else:
            sents.append(current_sent)
            current_sent = str(ns)
        current_index = ni

    if(len(current_sent)):
        sents.append(current_sent)
    
    return sre.sub(' ', ' '.join(sents))

@cython.cfunc
def mp_summary(full_data, important_words, full_summary, data, *, mp=True):
    try:
        text = data.get('text', '')

        if(type(text) != str):
            text = '\n'.join(text)

        if(not 3 < len(text) < 100_000):
            return ''

        data['summary'] = text_summary = summarize_by_keywords(text, important_words)

        full_summary.append(text_summary)

        full_data.append(text)
    except Exception as err:
        print(err)
    finally:
        if(mp):
            data["locks"] -= 1 

@cython.cfunc
def mp_all_summary(text, important_words, full_summary):
    try:
        if(type(text) != str):
            text = '\n'.join(text)

        text_summary = summarize_by_keywords(text, important_words)

        full_summary.append(text_summary)

    except Exception as err:
        print(err)

async def summarize_all(all_summaries: list, important_words: set, pool=None, *, max_len: int=90_000) -> str:
    if(not len(all_summaries)):
        return ''
    if(pool is not None):
        all_summaries = pool._manager.list(all_summaries)
        summary_q = pool._manager.list()
    else:
        summary_q = []
    current_summmary: list = []
    current_tokens: int = 0
    while len(all_summaries) != 1:
        all_summaries, summary_q = summary_q, all_summaries

        while(len(summary_q)):
            summary = summary_q[-1]
            current_tokens += len(summary)
            
            if current_tokens < max_len:
                current_summmary.append(summary)
                summary_q.pop()
            else:
                all_summaries.append(' '.join(current_summmary))
                current_summmary.clear()
                current_tokens = 0
        if(len(current_summmary)):
            all_summaries.append(' '.join(current_summmary))
            current_summmary.clear()
            current_tokens = 0

        # compute summaries
        if(pool is not None):
            args = [(summ,important_words,all_summaries) for summ in all_summaries]
            for _ in range(len(all_summaries)):
                all_summaries.pop()
            pool.starmap(mp_all_summary, args)
        else:
            args = all_summaries.copy()
            all_summaries.clear()
            for summary in args:
                mp_all_summary(summary, important_words, all_summaries)

    return all_summaries[0]


async def full_summary(crawler:Crawler):
    all_files = []

    queries_ = crawler.storage_data.get("Search", [])
    queries = [q[1].get('keywords') for q in queries_ if q[0] == 'query']

    important_words: set = get_important_words(queries)

    path:str
    dirs:list
    files:list
    for path, dirs, files in os.walk(crawler.storage_path):
        for file in files:
            all_files.append(file)

    if(crawler._resources is not None):
        full_data = crawler._resources._manager.list()
        full_summary = crawler._resources._manager.list()
    else:
        full_data = []
        full_summary = []

    website: str
    data: dict
    storage_data: list = [
        (full_data, important_words, full_summary, data[1]) 
        for pending_data in crawler.storage_data.values() 
            for data in pending_data
                if "text" in data[1]
    ]
    
    use_mp = False
    for data_ind, all_data in enumerate(storage_data):
        data = all_data[3]
        if(type(data) == dict):
            for all_data in storage_data[:data_ind]:
                with data._mutex:
                    data["locks"] = max(0, data["locks"] - 1)
            break
        with data._mutex:
            data["locks"] = data.get("locks", 0) + 1
    else:
        use_mp = True
    
    if(use_mp):
        crawler.resources_pool.starmap(mp_summary, storage_data, len(storage_data)//16 or 1)
    else:
        for data in storage_data:
            mp_summary(data, mp=False)

    await crawler.add_data("Full_summary", ("from_websites", {'urls': all_files}))
    await crawler.add_data("Full_summary", ("full_data", {'full_data':'\n'.join(full_data)}))
    await crawler.add_data("Full_summary", ("full_data", {'full_summary':'\n'.join(full_summary)}))
    #await crawler.add_data("Full_summary", ("full_summary", {'summary':await summarize_all(full_summary, important_words, crawler.resources_pool)}))
    await crawler.add_data("Full_summary", ("important_words", important_words))


def setup(crawler:Crawler):
    if(crawler.get_text not in crawler._page_management):
        crawler.add_pipe("page", crawler.get_text, "Text extractor")
    if(full_summary not in crawler._post_management):
        crawler.add_pipe("post", full_summary, "Full search summary")
