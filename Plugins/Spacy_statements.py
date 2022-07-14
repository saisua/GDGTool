# distutils: language=c++

from Core.Crawler import Crawler

import spacy


nlp = spacy.load("en_core_web_sm")

async def analize(crawler:Crawler, data:dict, page:object):
    doc = spacy.nlp(await page.frame.evaluate("document.body.innerText"))

    # Using spacy, resolve all coreferences

