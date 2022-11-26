# distutils: language=c++

import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Crawler import Crawler

### Sumarization ###


import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')

#export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
import spacy
nlp = spacy.load("en_core_web_md")

import gensim
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from nltk.stem import WordNetLemmatizer, SnowballStemmer
from nltk.stem.porter import *
from nltk.corpus import wordnet
import numpy as np

import wikipedia

from sortedcontainers import SortedList

from itertools import chain

def lemmatize_stemming(text):
    stemmer = SnowballStemmer('english')
    return stemmer.stem(WordNetLemmatizer().lemmatize(text, pos='v'))
def preprocess(text):
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3:
            result.append(token)
    return result


def simy(word, query):
    return query.similarity(nlp(word))
def get0(l): return l[0]

allowed_ents = {
  "PERSON",
  "LOC"
}


def spacy_most_similar(word, topn=10):
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


def join_sents(s1, s2):
    return f"{s1} {s2}"


sre = re.compile('\s+')
def summarize_by_keywords(text, keywords, *, sentences: int=10):
    text_doc = nlp(text)
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


async def full_summary(crawler:Crawler):
    all_files = []
    full_data = []
    full_summary = []

    queries_ = crawler.storage_data.get("Search", [])
    queries = list(chain(*[q[1].get('keywords') for q in queries_ if q[0] == 'query']))

    important_words = get_important_words(queries)

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
            if(not 'text' in data):
                continue
            all_files.append(website)
            text = data.get('text', '')

            if(type(text) != str):
                text = '\n'.join(text)

            if(len(text) == 0):
                continue

            data['summary'] = text_summary = summarize_by_keywords(text, important_words)

            full_summary.append(text_summary)

            full_data.append(text)

    await crawler.add_data("Full_summary", ("from_websites", {'urls': all_files}))
    await crawler.add_data("Full_summary", ("full_data", {'full_data':'\n'.join(full_data)}))
    await crawler.add_data("Full_summary", ("full_data", {'full_summary':'\n'.join(full_summary)}))
    await crawler.add_data("Full_summary", ("full_summary", {'summary':summarize_by_keywords('\n'.join(full_summary), important_words)}))
    await crawler.add_data("Full_summary", ("important_words", important_words))


###

async def basic_search():
    query = "Aragorn the lord of the rings"

    async with Crawler(storage_name=f"{query} search", remove_old_data=True, headless=False) as cr:
        await cr.search(query)
        cr.add_pipe("page", cr.get_text, "Text extractor")
        cr.add_pipe("post", full_summary, "Full summary")
        await cr.crawl(levels=1, max_tabs=5, max_websites=20)

if(__name__ == "__main__"):
    asyncio.run(basic_search())