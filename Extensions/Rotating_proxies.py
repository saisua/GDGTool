# distutils: language=c++

from itertools import cycle

import cython

class Rotating_proxies:
    rotating_child:object
    _rotating_proxies:list
    __rotating_proxy:object

    Rotating_proxies_init:cython.bint

    

    def __init__(self, child:"Browser", *args, **kwargs):
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Rotating proxies")

        self.rotating_child = child
        self._rotating_proxies = kwargs.pop("proxies", [])
        self.Rotating_proxies_init = True
        print("Init rotating proxies")


    async def get_proxies_online(self, type:str="http", country:str="all", anonimity:str="all"):
        browser:object = await self.rotating_child._playwright_manager.chromium.launch(headless=True)
        page:object = await browser.new_page()
        res:object = await page.goto(("https://api.proxyscrape.com/?request=share&proxytype=http&timeout=10000&"
                                f"country={country}&ssl=yes&anonymity={anonimity}"),
                                wait_until="networkidle")

        while(res is None):
            res = await page.goto(("https://api.proxyscrape.com/?request=share&proxytype=http&timeout=10000&"
                                f"country={country}&ssl=yes&anonymity={anonimity}"),
                                wait_until="networkidle")

        self._rotating_proxies.extend([f"{type}://{p}" for p in (await res.frame.evaluate("()=>document.querySelector('textarea').defaultValue")).split()])
        await page.close()

        self.__rotating_proxy = cycle(self._rotating_proxies)

    def new_proxy(self):
        return next(self.__rotating_proxy)