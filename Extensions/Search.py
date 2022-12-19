# distutils: language=c++

from typing import Union, Iterable
import cython

# Not using Yahoo since it requires additional steps
SEARCH_GENERAL: list = ["https://www.google.com/search?q={}",
                "https://duckduckgo.com/?q={}",
                #"https://www.bing.com/search?q={}",
                "https://en.wikipedia.org/wiki/{}"
]

SEARCH_IMAGES: list = ["https://www.google.com/search?tbm=isch&q={}",
                "https://duckduckgo.com/?iax=images&ia=images&q={}",
                "https://www.bing.com/images/search?q={}"
]

SEARCH_VIDEOS: list = ["https://www.bing.com/videos/search?q={}",
                "https://duckduckgo.com/?iax=videos&ia=videos&q={}",    
                "https://www.google.com/search?tbm=vid&q={}",
                "https://www.youtube.com/results?search_query={}",
                "https://www.twitch.tv/search?term={}&type=videos"
]
                
SEARCH_NEWS: list = ["https://www.google.com/search?tbm=nws&q={}",
                "https://www.bing.com/news/search?q={}",
                "https://duckduckgo.com/?iar=news&ia=news&q={}"
]

SEARCH_SHOPPING: list = ["https://www.google.com/search?tbm=shop&q={}",
]

SEARCH_MAPS: list = ["https://duckduckgo.com/?iaxm=maps&ia=web&q={}",
                "https://www.google.com/maps/search/{}/"
]

SEARCH_SOCIAL: list = ["https://twitter.com/search?q={}",
                "https://facebook.com/public/{}",
                "https://www.google.com/search?q={}+site%3Ainstagram.com",
                "https://duckduckgo.com/?q={}+site%3Ainstagram.com",
                "https://www.bing.com/search?q={}+site%3Ainstagram.com"
]


__search_list: list = [varname for varname in globals().keys() if varname.startswith("SEARCH_")]


_get_dict: dict = {"default":SEARCH_GENERAL, 
            "*":[link for links in [globals()[varname] for varname in __search_list] for link in links],
            **{varname[7:].lower():globals()[varname] for varname in __search_list}}


class Search:
    search_child:object
    valid_search_contexts:set

    def __init__(self, child:object, *args, **kwargs) -> None:
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Search")

        self.valid_search_contexts = set(_get_dict.keys())
        self.search_child = child

        if("search_area" in kwargs):
            if(kwargs.get("clear_search", False)):
                _get_dict.clear()
            _get_dict.update(kwargs["search_area"])

        assert self.valid_search_contexts is not None
        assert self.search_child is not None

    def __add_links(self, new_links:Iterable, keywords:Union[str, Iterable], block_start_domains:bool=True) -> list:
        kw_is_str = type(keywords) is str
        links: list = []
        for link in new_links:
            _link: str
            _links: list
            if(kw_is_str):
                _link = link.format(keywords)
                links.append(_link)
            else:
                _links = [link.format(word) for word in keywords]
                links.extend(_links)
            
            if(self.search_child.Crawler_init):
                self.search_child.crawler_visited_urls.add(link)
                domain = self.search_child.crawler_domain_regex.match(link).group(3)
                if(domain not in self.search_child.crawler_sites):
                    self.search_child.crawler_sites[domain] = set()
                    if(block_start_domains):
                        self.search_child.crawler_blocked_domains.add(domain)

                if(kw_is_str):
                    self.search_child.crawler_sites[domain].add(_link)
                else:
                    self.search_child.crawler_sites[domain].update(_links)
        
        return links

    async def search(self, keywords:Union[str, Iterable], 
                    search_in:Union[str, Iterable[Union[Iterable[str],str]]] = "default",
                    block_start_domains:bool=True) -> list:
        if(not keywords or not search_in): return

        if(isinstance(keywords, str)): keywords = [keywords]

        if(isinstance(search_in, str)):
            new_links = _get_dict.get(search_in, [search_in])
        elif(isinstance(search_in, Iterable)):
            new_links = set()
            for sub in search_in:
                if(isinstance(sub, str)):
                    new_links.update(_get_dict.get(search_in, [search_in]))
                elif(isinstance(sub, Iterable)):
                    new_links.update(sub)
                else: raise ValueError("Search (sub) parameters were wrong. Check search args")
        else: raise ValueError("Search parameters were wrong. Check search args")

        links = self.__add_links(new_links, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))

        return links

    async def search_general(self, keywords:Union[str, Iterable], site:str=None, block_start_domains:bool=True) -> list:
        links: list
        if(site is not None):
            links = self.__add_links((f"{link}+site:{site}" for link in SEARCH_GENERAL), keywords, block_start_domains)
        else:
            links = self.__add_links(SEARCH_GENERAL, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))

        return links
        
    async def search_images(self, keywords:Union[str, Iterable], block_start_domains:bool=True) -> list:
        links = self.__add_links(SEARCH_IMAGES, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))

        return links

    async def search_videos(self, keywords:Union[str, Iterable], block_start_domains:bool=True) -> list:
        links = self.__add_links(SEARCH_VIDEOS, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))

        return links
        
    async def search_news(self, keywords:Union[str, Iterable], block_start_domains:bool=True) -> list:
        links = self.__add_links(SEARCH_NEWS, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))

        return links

    async def search_shopping(self, keywords:Union[str, Iterable], block_start_domains:bool=True) -> list:
        links = self.__add_links(SEARCH_SHOPPING, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))
        
        return links

    async def search_maps(self, keywords:Union[str, Iterable], block_start_domains:bool=True) -> list:
        links = self.__add_links(SEARCH_MAPS, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))

        return links
        
    async def search_social(self, keywords:Union[str, Iterable], block_start_domains:bool=True) -> list:
        links = self.__add_links(SEARCH_SOCIAL, keywords, block_start_domains)

        if(self.search_child.Storage_init):
            await self.search_child.add_data("Search", ('query', {"keywords":keywords}))

        return links

#def search_recipes(keywords:Union[str, Iterable]):
