from typing import Union, Iterable
from xml import dom


# Not using Yahoo since it requires additional steps
SEARCH_GENERAL = ["https://www.google.com/search?q={}",
                "https://duckduckgo.com/?q={}",
                "https://www.bing.com/search?q={}",
                "https://en.wikipedia.org/wiki/{}"]

SEARCH_IMAGES = ["https://www.google.com/search?tbm=isch&q={}",
                "https://duckduckgo.com/?iax=images&ia=images&q={}",
                "https://www.bing.com/images/search?q={}"]

SEARCH_VIDEOS = ["https://www.bing.com/videos/search?q={}",
                "https://duckduckgo.com/?iax=videos&ia=videos&q={}",    
                "https://www.google.com/search?tbm=vid&q={}",
                "https://www.youtube.com/results?search_query={}",
                "https://www.twitch.tv/search?term={}&type=videos"]
                
SEARCH_NEWS = ["https://www.google.com/search?tbm=nws&q={}",
                "https://www.bing.com/news/search?q={}",
                "https://duckduckgo.com/?iar=news&ia=news&q={}"]

SEARCH_SHOPPING = ["https://www.google.com/search?tbm=shop&q={}",]

SEARCH_MAPS = ["https://duckduckgo.com/?iaxm=maps&ia=web&q={}",
                "https://www.google.com/maps/search/{}/"]

SEARCH_SOCIAL = ["https://twitter.com/search?q={}",
                "https://facebook.com/public/{}",
                "https://www.google.com/search?q={}+site%3Ainstagram.com",
                "https://duckduckgo.com/?q={}+site%3Ainstagram.com",
                "https://www.bing.com/search?q={}+site%3Ainstagram.com"]


__search_list = [varname for varname in globals().keys() if varname.startswith("SEARCH_")]


_get_dict = {"default":SEARCH_GENERAL, 
            "*":[link for links in [globals()[varname] for varname in __search_list] for link in links],
            **{varname[7:].lower():globals()[varname] for varname in __search_list}}


class Search():
    child:object
    valid_search_contexts:set = set(_get_dict.keys())

    def __init__(self, child:object, *args, **kwargs) -> None:
        self.child = child
        if("search_area" in kwargs):
            if(kwargs.get("clear_search", False)):
                _get_dict.clear()
            _get_dict.update(kwargs["search_area"])

    def __add_links(self, new_links:Iterable, keywords:Union[str, Iterable], block_start_domains:bool=True) -> None:
        kw_is_str = type(keywords) is str
        for link in new_links:
            self.child.visited_urls.add(link)

            domain = self.child.domain_regex.match(link).group(3)
            if(domain not in self.child.sites):
                self.child.sites[domain] = set()
                if(block_start_domains):
                    self.child.blocked_domains.add(domain)

            if(kw_is_str):
                self.child.sites[domain].add(link.format(keywords))
            else:
                self.child.sites[domain].update((link.format(word) for word in keywords))

    async def search(self, keywords:Union[str, Iterable], 
                    search_in:Union[str, Iterable[Union[Iterable[str],str]]] = "default",
                    block_start_domains:bool=True) -> None:
        if(not keywords or not search_in): return

        if(isinstance(keywords, str)): keywords = [keywords]

        if(isinstance(search_in, str)):
            new_links = _get_dict.get(search_in, [search_in])
        elif(isinstance(search_in, Iterable)):
            new_links = []
            for sub in search_in:
                if(isinstance(sub, str)):
                    new_links.extend(_get_dict.get(search_in, [search_in]))
                elif(isinstance(sub, Iterable)):
                    new_links.extend(sub)
                else: raise ValueError("Search (sub) parameters were wrong. Check search args")
        else: raise ValueError("Search parameters were wrong. Check search args")

        self.__add_links(new_links, keywords, block_start_domains)

    async def search_general(self, keywords:Union[str, Iterable], site:str=None, block_start_domains:bool=True) -> None:
        if(site is not None):
            self.__add_links((f"{link}+site:{site}" for link in SEARCH_GENERAL), keyword, block_start_domainss)
        else:
            self.__add_links(SEARCH_GENERAL, keywords, block_start_domains)

    async def search_images(self, keywords:Union[str, Iterable], block_start_domains:bool=True):
        self.__add_links(SEARCH_IMAGES, keywords, block_start_domains)
                                                
    async def search_videos(self, keywords:Union[str, Iterable], block_start_domains:bool=True):
        self.__add_links(SEARCH_VIDEOS, keywords, block_start_domains)

    async def search_news(self, keywords:Union[str, Iterable], block_start_domains:bool=True):
        self.__add_links(SEARCH_NEWS, keywords, block_start_domains)

    async def search_shopping(self, keywords:Union[str, Iterable], block_start_domains:bool=True):
        self.__add_links(SEARCH_SHOPPING, keywords, block_start_domains)

    async def search_maps(self, keywords:Union[str, Iterable], block_start_domains:bool=True):
        self.__add_links(SEARCH_MAPS, keywords, block_start_domains)

    async def search_social(self, keywords:Union[str, Iterable], block_start_domains:bool=True):
        self.__add_links(SEARCH_SOCIAL, keywords, block_start_domains)

#def search_recipes(keywords:Union[str, Iterable]):
