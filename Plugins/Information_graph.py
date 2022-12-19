try:
    from Core.Crawler import Crawler
except ModuleNotFoundError:
    Crawler = "Crawler"

import os
import pickle
import asyncio

import spacy, coreferee
nlp = spacy.load("en_core_web_md")
nlp.add_pipe('coreferee')

import nltk

from nltk.corpus import wordnet

import numpy as np 
import cython

from collections import Counter
from sortedcontainers import SortedList
import re

s_re = re.compile("\s+")
w_re = re.compile("[ \w]+")

try:
    from Plugins.utils.coref_resolution import solve_coref
except ModuleNotFoundError:
    from utils.coref_resolution import solve_coref

stopw = spacy.lang.en.stop_words.STOP_WORDS
fpos = {
  "PUNCT",
  "INTJ",
  "X"
}

def get1(c:tuple)->int: return c[1]

class Nrel:
  data: str
  prev: dict
  next: dict
  __slots__ = [
  "data",
  "prev",
  "next"
  ]
  def __init__(self,
      data: str, *,
      prev: bool = False,
      next: bool = False
    ):
    self.data = data
    self.prev = dict() if prev else None
    self.next = dict() if next else None
  def update(self, new) -> None:
    assert new.__class__ == self.__class__
    assert self.data == new.data

    if(new.prev is not None):
      if(self.prev is None):
        self.prev = new.prev
      else:
        for rel, relW in new.prev.items():
          self.prev[rel] = self.prev.get(rel, 0) + relW

    if(new.next is not None):
      if(self.next is None):
        self.next = new.next
      else:
        for rel, relW in new.next.items():
          self.next[rel] = self.next.get(rel, 0) + relW
  def add_next(self, rel, *, count: int=1):
    self.next[rel] = self.next.get(rel, 0) + count
  def add_prev(self, rel, *, count: int=1):
    self.prev[rel] = self.prev.get(rel, 0) + count
  def add_both(self, prev, next, *, count: int=1):
    self.prev[prev] = self.prev.get(prev, 0) + count
    self.next[next] = self.next.get(next, 0) + count
  def __hash__(self):
    return self.data.__hash__()
  def __eq__(self, new):
    return (
      self.__class__ == new.__class__
      and
      self.data == new.data
    )
  def __str__(self):
    return self.data
  def __contains__(self, substr: str):
    return substr in self.data
  def _sort(self):
    if(self.prev is not None):
      self.prev = dict(sorted(self.prev.items, key=get1))
    if(self.next is not None):
      self.next = dict(sorted(self.next.items, key=get1))

class Nbase:
  subj: dict
  root: dict
  obj: dict
  __slots__ = [
  "subj",
  "root",
  "obj"
  ]
  def __init__(self):
    self.subj = dict()
    self.root = dict()
    self.obj = dict()
  def new_subj(self,
      data: str,
      *,
      root: Nrel=None,
      root_count: int=1
    ) -> Nrel:
    entry: Nrel = self.subj.get(data)
    if(entry is None):
      entry = Nrel(data, next=True)
      self.subj[entry] = entry
    if(root is not None):
      entry.add_next(root, count=root_count)
    return entry
  def new_root(self,
      data: str,
      *,
      subj: Nrel=None,
      subj_count: int=1,
      obj: Nrel=None,
      obj_count: int=1
    ) -> Nrel:
    entry: Nrel = self.root.get(data)
    if(entry is None):
      entry = Nrel(data, prev=True, next=True)
      self.root[entry] = entry
    if(subj is not None):
      entry.add_prev(subj, count=subj_count)
    if(obj is not None):
      entry.add_next(obj, count=obj_count)
    return entry
  def new_obj(self,
      data: str,
      *,
      root: Nrel=None,
      root_count: int=1
    ) -> Nrel:
    entry: Nrel = self.obj.get(data)
    if(entry is None):
      entry = Nrel(data, prev=True)
      self.obj[entry] = entry
    if(root is not None):
      entry.add_prev(root, count=root_count)
    return entry
  def new_rel(self,
      subj: str,
      root: str,
      obj: str,
      *,
      count: int=1
    ):
    subj_entry: Nrel = self.subj.get(subj)
    if(subj_entry is None):
      subj_entry = Nrel(subj, next=True)
      self.subj[subj_entry] = subj_entry
    root_entry: Nrel = self.root.get(root)
    if(root_entry is None):
      root_entry = Nrel(root, prev=True, next=True)
      self.root[root_entry] = root_entry
    obj_entry: Nrel = self.obj.get(obj)
    if(obj_entry is None):
      obj_entry = Nrel(obj, prev=True)
      self.obj[obj_entry] = obj_entry

    subj_entry.add_next(root_entry, count=count)
    root_entry.add_both(subj_entry, obj_entry, count=count)
    obj_entry.add_prev(root_entry, count=count)
  def update(self, new) -> None:
    assert new.__class__ == self.__class__

    rel: Nrel
    srel: Nrel
    if(new.subj is not None):
      if(self.subj is None):
        self.subj = new.subj
      else:
        for rel in new.subj.keys():
          srel = self.subj.get(rel)
          if(srel is None):
            self.subj[rel] = rel
          else:
            srel.update(rel)
    if(new.root is not None):
      if(self.root is None):
        self.root = new.root
      else:
        for rel in new.root.keys():
          srel = self.root.get(rel)
          if(srel is None):
            self.root[rel] = rel
          else:
            srel.update(rel)
    if(new.obj is not None):
      if(self.obj is None):
        self.obj = new.obj
      else:
        for rel in new.obj.keys():
          srel = self.obj.get(rel)
          if(srel is None):
            self.obj[rel] = rel
          else:
            srel.update(rel)
  def update_by_filter(self, 
      new,
      ffilter,
      *,
      subj: bool = True,
      root: bool = True,
      obj: bool = True
    ):
    assert new.__class__ == self.__class__

    rel: Nrel
    srel: Nrel
    if(subj and new.subj is not None):
      if(self.subj is None):
        self.subj = {
          k:k
          for k in new.subj.keys()
            if ffilter(k)
        }
      else:
        for rel in new.subj.keys():
          if(not ffilter(rel)):
            continue
          srel = self.subj.get(rel)
          if(srel is None):
            self.subj[rel] = rel
          else:
            srel.update(rel)
    if(root and new.root is not None):
      if(self.root is None):
        self.root = {
          k:k
          for k in new.root.keys()
            if ffilter(k)
        }
      else:
        for rel in new.root.keys():
          if(not ffilter(rel)):
            continue
          srel = self.root.get(rel)
          if(srel is None):
            self.root[rel] = rel
          else:
            srel.update(rel)
    if(obj and new.obj is not None):
      if(self.obj is None):
        self.obj = {
          k:k
          for k in new.obj.keys()
            if ffilter(k)
        }
      else:
        for rel in new.obj.keys():
          if(not ffilter(rel)):
            continue
          srel = self.obj.get(rel)
          if(srel is None):
            self.obj[rel] = rel
          else:
            srel.update(rel)
    
  @property
  def network_graph(self, *, sorted=False):
    traces = list()
    root_nums = dict()
    obj_nums = dict()
    
    for subj_num, subj in enumerate(self.subj.keys()):
      if(sorted):
        subj._sort()

      for root, root_w in subj.next.items():
        root_num = root_nums.get(root)
        if(root_num is None):
          root_num = root_nums[root] = len(root_nums)

          if(sorted):
            root._sort()

        for obj, obj_w in root.next.items():
          obj_num = obj_nums.get(obj)
          if(obj_num is None):
            obj_num = obj_nums[obj] = len(obj_nums)

          traces.append({
            'x':[0, 1, 2],
            'y':np.array([subj_num, root_num, obj_num]),
            'mode':"markers+lines",
            'name':f"{subj} -{root_w}- {root} -{obj_w}- {obj}",
            'text':list(map(str, (subj, root, obj)))
          })

    lens = np.array([
      len(self.subj),
      len(root_nums),
      len(obj_nums)
    ])
    maxn = np.max(lens)

    for trace in traces:
      trace['y'] = trace['y'] / lens * maxn

    return traces

def geti(word):
  return word.i

def is_valid_child(child):
  return ( child.dep_ in {
    "compound",
    "aux"
  } or "subj" in child.dep_
  and child.pos_ not in fpos
  )


# Handle the subj - root - obj relationships when
# the root is not the verb 'to be'
def handle_nsis(obj):
  obj_queues = []
  tmp_q = []
  for tok in obj:
    if(tok.pos_ == "PUNCT"):
      if(len(tmp_q)):
        obj_queues.append(tmp_q.copy())
        tmp_q.clear()
    else:
      tmp_q.append(tok)
  if(len(tmp_q)):
    obj_queues.append(tmp_q)

  return Counter((' '.join(map(str, obj_q)) for obj_q in obj_queues))

# Handle the subj - root - obj relationships when
# the root is the special case verb 'to be'
def special_is(subj_str, subj_list, root_str, root_list, obj):
    obj_relations = handle_nsis(obj)
    obj_inv_relations = Counter()
    obj_adj_relations = Counter()
    for obj_as_subj_str in obj_relations.copy():
        obj_inv_relations[obj_as_subj_str] += 1

        inv_obj = nlp(obj_as_subj_str)
        non_adj = [t for t in inv_obj if t.pos_ != "ADJ"]
        adjectives = [t for t in inv_obj if t.pos_ == "ADJ"]

        inv_non_adj = None
        if(len(non_adj) and len(non_adj) != len(inv_obj)):
            inv_non_adj = ' '.join(map(str, non_adj))
            #print(f"{subj_str} -> {root_str} -> {inv_non_adj}")
            #print(f"{inv_non_adj} -> {root_str} -> {subj_str}")
            obj_relations[inv_non_adj] += 1
            obj_inv_relations[inv_non_adj] += 1

        if(len(adjectives) != len(inv_obj)):
            for adj in adjectives:
                adj_str = str(adj)
                #print(f"{subj_str} -> {root_str} -> {adj_str}")

                obj_relations[adj_str] += 1

                if(inv_non_adj is not None):
                    #print(f"{inv_non_adj} -> {root_str} -> {adj_str}")

                    obj_adj_relations[(inv_non_adj, adj_str)] += 1

    return obj_relations, obj_inv_relations, obj_adj_relations



def compute_graph(text):
    solved_doc = nlp(s_re.sub(' ', solve_coref(nlp(text))))

    ## Compute the subject for each sentence
    subjects = dict()
    for token in solved_doc:
        if('subj' in token.dep_):
            sorted_subj_children = SortedList(key=geti)
            children_q = [token]
            while(len(children_q)):
                child = children_q.pop()
                sorted_subj_children.add(child)
                children_q.extend((child_ for child_ in child.children if is_valid_child(child)))

            subj_str = (str(child) for child in sorted_subj_children if child.pos_ not in fpos)
            subj_str = [word_str for word_str in subj_str if word_str not in stopw and w_re.match(word_str)]
            if(len(subj_str)):
                subj_str = ' '.join(subj_str).strip().lower()

                subjects_list = subjects.get(subj_str)
                if(subjects_list is not None):
                    subjects_list.append(sorted_subj_children)
                else:
                    subjects[subj_str] = [sorted_subj_children]
    ##

    ## Compute the roots (and subj - root relationship) for each sentence
    relations = {}
    roots = {}
    for subj_str, subj_list in subjects.items():
        for token_sentence in subj_list:
            for token in token_sentence:
                ancestors = list(token.ancestors)
                child = None
                while(len(ancestors)):
                    ancestor = ancestors.pop(0)
                    if(ancestor.dep_ == "ROOT"):
                        child = ancestor
                        ancestors.clear()
                        break
                    ancestors.extend(ancestor.ancestors)
                if(child is not None):
                    sorted_root_children = SortedList(key=geti)
                    root_q = [child]
                    while(len(root_q)):
                        child = root_q.pop()
                        sorted_root_children.add(child)
                        root_q.extend((child for child in child.children if child.dep_ == "aux"))

                    root_str = ' '.join((rr.lemma_ for rr in sorted_root_children))
                    if(subj_str not in relations):
                            relations[subj_str] = {root_str: [(token_sentence, sorted_root_children)]}
                    elif(root_str not in relations[subj_str]):
                        relations[subj_str][root_str] = [(token_sentence, sorted_root_children)]
                    else:
                        relations[subj_str][root_str].append((token_sentence, sorted_root_children))

                    if(root_str not in roots):
                        roots[root_str] = [sorted_root_children]
                    else:
                        roots[root_str].append(sorted_root_children)

                    #print(f"{subj_str} -> {root_str}")
                    break
                ancestors.clear()
    ##

    ## Compute the objects (and subj - root - obj relationship) for each sentence

    relationship_network = Nbase()
    for subj_str, relation_dict in relations.items():
        for root_str, relation_list in relation_dict.items():
            for (subj_list, root_list) in relation_list:
                found_tokens = set((*subj_list, *root_list))
                sorted_obj_children = SortedList(key=geti)
                first_root_i = next((root_tok.i for root_tok in root_list if root_tok.dep_ == "ROOT"))
                obj_q = list((
                    child for root_tok in root_list
                        for child in root_tok.children
                            if child.i > first_root_i and child not in found_tokens
                ))
                while(len(obj_q)):
                    obj_tok = obj_q.pop()
                    found_tokens.add(obj_tok)
                    sorted_obj_children.add(obj_tok)
                    obj_q.extend((child for child in obj_tok.children if child.i > first_root_i and child not in found_tokens))

                obj_str = ' '.join(map(str, sorted_obj_children))
                if(len(sorted_obj_children)):
                    clean_obj = list((obj_tok for obj_tok in sorted_obj_children if obj_tok.pos_ != "PART"))
                    if(root_str == 'be' and len(clean_obj) and clean_obj[0].pos_ not in {"VERB", "ADP"}):
                        obj_rels, obj_inv_rels, obj_adj_rels = special_is(subj_str, subj_list, root_str, root_list, sorted_obj_children)
                        for obj_str, count in (*obj_rels.items(), *obj_inv_rels.items()):
                            relationship_network.new_rel(subj_str, root_str, obj_str, count=count)
                        for (adj_subj, adj_obj), count in obj_adj_rels.items():
                            relationship_network.new_rel(adj_subj, root_str, adj_obj, count=count)

                    else:
                        for obj_str, count in handle_nsis(sorted_obj_children).items():
                            relationship_network.new_rel(subj_str, root_str, obj_str, count=count)

                else:
                    #print(f"{subj_str} -> {root_str} -> {obj_str}")
                    relationship_network.new_rel(subj_str, root_str, obj_str)

    return relationship_network

def mp_graph(data, all_networks,  *, mp: bool=True):
    try:
        text = data.get('text', '')

        if(type(text) != str):
            text = '\n'.join(text)

        if(not 3 < len(text) < 100_000):
            return ''

        network = compute_graph(text)
        data['graph_pickle'] = pickle.dumps(network)
        all_networks.append(network)
    
    except Exception as err:
        print(err)
    finally:
        if(mp):
            data["locks"] -= 1 

async def generate_graph(crawler:Crawler):
    all_files = []

    path:str
    dirs:list
    files:list
    for path, dirs, files in os.walk(crawler.storage_path):
        for file in files:
            all_files.append(file)

    if(crawler._resources is not None):
        full_data = crawler._resources._manager.list()
        full_graph = crawler._resources._manager.list()
    else:
        full_data = []
        full_graph = []

    website: str
    data: dict
    storage_data: list = [
        (data[1], full_graph) 
        for pending_data in crawler.storage_data.values() 
            for data in pending_data
                if "text" in data[1]
    ]
    
    use_mp = False
    for data_ind, all_data in enumerate(storage_data):
        data = all_data[0]
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
        crawler.resources_pool.starmap(mp_graph, storage_data, len(storage_data)//16 or 1)
    else:
        for data in storage_data:
            mp_graph(*data, mp=False)

    full_network = Nbase()
    for graph in full_graph:
        full_network.update(graph)

    from plotly.graph_objects import Figure
    fig = Figure()
    for graph in full_network.network_graph:
        fig.add_scatter(**graph)
    fig.show()

    await crawler.add_data("Information_graph", ("from_websites", {'urls': all_files}))
    await crawler.add_data("Information_graph", ("full_graph", {'full_graph':full_network}))

def setup(crawler:Crawler):
    if(crawler.get_text not in crawler._page_management):
        crawler.add_pipe("page", crawler.get_text, "Text extractor")
    if(generate_graph not in crawler._post_management):
        crawler.add_pipe("post", generate_graph, "Full search information graph")
