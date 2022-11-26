# distutils: language=c++

import asyncio
import cython
import multiprocessing as mp
from playwright._impl._api_types import TimeoutError

import inspect

class Resources:
    _manager:mp.Manager
    resources_pool:mp.Pool

    Resources_init:cython.bint

    

    def __init__(self, *args, **kwargs):
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Resources")

        self._manager = mp.Manager()
        self.resources_pool = self._manager.Pool(**{kw:v for kw, v in kwargs.items() if kw in {'processes'}})
        self.Resources_init = True

    async def __aenter__(self, *args, **kwargs):
        if(not self.Resources_init): return

        f_name:str
        for overwrite_f in dir(Resources)[::-1]:
            if(overwrite_f.startswith("override_")):
                f_name = overwrite_f[len('override_'):]
                if(hasattr(self, f_name)):
                    setattr(self, f_name, getattr(self, overwrite_f))
                    continue

                f_name = f"_{self.__class__.__name__}_{f_name}"
                if(hasattr(self, f_name)):
                    setattr(self, f_name, getattr(self, overwrite_f))
                    continue
            elif(overwrite_f.startswith("__")): break

    async def __aexit__(self, *args, **kwargs):
        if(not self.Resources_init): return

        self.resources_pool.close()
        self.resources_pool.join()

    async def override__manage_website(self, tab, url):
        try:
            loaded_site = await tab.goto(url)
        except TimeoutError:
            return 
    
        if(loaded_site is not None): 
            loaded_site.domain = self.domain_regex.match(loaded_site.url).group(3)

            website_data:dict = {}
            # In case of dynamically loaded websites

            for _ in asyncio.as_completed([page_alter(self, website_data, loaded_site) for page_alter in self._page_management]):
                await _

            mp_website_data:object = self._manager.dict(website_data)
            for _ in asyncio.as_completed([data_alter(self, mp_website_data, loaded_site) for data_alter in self._data_management]):
                await _

            if("urls" in website_data):
                for site in website_data["urls"]:
                    if(site not in self.visited_urls):
                        self.visited_urls.add(site)

                        match = self.domain_regex.search(site)
                        if(match):
                            domain = match.group(3)
                            if(domain not in self.blocked_domains):
                                if(domain not in self.sites):
                                    self.next_level_sites[domain] = {site}
                                else:
                                    self.next_level_sites[domain].add(site)
            
            if("locks" in mp_website_data):
                asyncio.create_task(self._mp_add_data(mp_website_data, loaded_site.domain, (loaded_site.url, mp_website_data)))
            else:
                asyncio.create_task(self.add_data(loaded_site.domain, (loaded_site.url, mp_website_data)))
            
        self._avaliable_tabs.append(tab)


    async def _mp_add_data(self, mp_website_data, *args, **kwargs):
        while(mp_website_data["locks"]):
            await asyncio.sleep(1)

        mp_website_data.pop("locks")
        await self.add_data(*args, **kwargs)

    def _retry_load_website(self, page, site):
        page.goto(site, timeout=0)