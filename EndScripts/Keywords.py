# distutils: language=c++
import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('stopwords')

#export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
import spacy, coreferee, pytextrank, spacy_fastlang
nlp = spacy.load("en_core_web_md")
nlp.add_pipe('coreferee')
nlp.add_pipe('textrank')
nlp.add_pipe("language_detector")

import numpy as np

import cython

import re

from itertools import chain

from collections import Counter

from EndScripts.utils.load_data import load_data
from EndScripts.utils.store_data import store_data

allowed_ents = {
  "PERSON",
  "LOC"
}

alphanum_re = re.compile('(\.{2,}| {2,}|[^A-z0-9.,-_])')
def get_keywords(texts: list, 
                 *,
                 get_top_keywords: int=3,
                 forbidden_substrings: set = {'wiki'}):
    print("Get keywords")
        
    sent_keywords = []
    sent_ents = Counter()
    for text in (
        t
        for t in (nlp(alphanum_re.sub(' ', tx)) for tx in texts)
            if t._.language == "en" and
                t._.language_score >= 0.5
        ):
        keywords = set()
        good_kw = list()
        for phrase in text._.phrases:
            ptext = phrase.text
            ltext = ptext.lower()

            if(
                    ltext not in keywords and 
                    not any((True for sstr in forbidden_substrings if sstr in ltext))
                ):
                keywords.add(ltext)
                good_kw.extend(phrase.chunks)
    
        sent_keywords.append(good_kw)
        sent_ents.update((ent for ent in (e.text.strip().lower() for e in text.ents if e.label_ in allowed_ents) if not any((True for sstr in forbidden_substrings if sstr in ent))))

    # Get those which contain entities but are not exactly repeated
    all_sent_count = Counter((s.text.strip().lower() for s in chain(*sent_keywords)))
    best = Counter()
    for text in sent_keywords:
        for phrase in text:
            tphrase = phrase.text

            if(all_sent_count.get(tphrase.strip().lower()) == 1):
                best[tphrase] = sum((count for ent, count in sent_ents.most_common() if ent in phrase.sent.text.strip().lower()))

    return [t[0] for t in best.most_common(get_top_keywords)]


def main(*args, queries: list=None, **kwargs):
    """Get the run folder for {Data_path}/{folder} and walk the directory tree 
       getting the most important keywords from the text in the files that match
       the folder_regex and then the file_regex

    Args:
        folder (str): The folder (stored execution folder)
        queries: (list, optional): List of query strings to use for the extraction
        folder_regex (Pattern, optional): The regex that matches what folders will be loaded
        file_regex (Pattern, optional): The regex that matches what JSON files will be loaded
        Data_path (str, optional): The base path to the Data folder. Defaults to "Data/".
        force (bool, optional): If the folder contains the 'keywords' file, whether to force the execution
    """
    data, base_folder = load_data(*args, **kwargs)

    if('keywords' in data and not kwargs.get('force', False)):
        return

    if(queries is None):
        search_folder = data.get("Search")
        if(search_folder is not None):
            query_json = search_folder.get('query')
            if(query_json is not None):
                queries = query_json.get('keywords')

    keywords = get_keywords(queries)

    store_data(keywords, base_folder)
