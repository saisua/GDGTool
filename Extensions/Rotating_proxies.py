from itertools import cycle

class Rotating_proxies:
    child:object
    _proxies:list
    __proxy:object

    def __init__(self, child:"Browser", *args, **kwargs):
        self.child = child
        self._proxies = kwargs.pop("proxies", [])
        setattr(self, "Rotating_proxies_init", True)
        print("Init rotating proxies")


    async def get_proxies_online(self, type:str="http", country:str="all", anonimity:str="all"):
        browser:object = await self.child._playwright_manager.chromium.launch(headless=True)
        page:object = await browser.new_page()
        res:object = await page.goto(("https://api.proxyscrape.com/?request=share&proxytype=http&timeout=10000&"
                                f"country={country}&ssl=yes&anonymity={anonimity}"),
                                wait_until="networkidle")

        while(res is None):
            res = await page.goto(("https://api.proxyscrape.com/?request=share&proxytype=http&timeout=10000&"
                                f"country={country}&ssl=yes&anonymity={anonimity}"),
                                wait_until="networkidle")

        self._proxies.extend([f"{type}://{p}" for p in (await res.frame.evaluate("()=>document.querySelector('textarea').defaultValue")).split()])
        await page.close()

        self.__proxy = cycle(self._proxies)

    def new_proxy(self):
        return next(self.__proxy)