import cython
import asyncio

class Children():
    children: list = []

    def __init__(self, children: tuple):
        self.children.extend(children)

    def __getattr__(self, attr: str):
        #print(f"Accessing {attr}", flush=False)
        for child in self.children:
            if(child is not None and hasattr(child, attr)):
                return getattr(child, attr)
            #elif(child is not None):
                #print(f" {child.__class__.__name__} has no \"{attr}\"", flush=False)

    async def __aenter__(self, *args, **kwargs):
        for _ in asyncio.as_completed([ch.__aenter__(self) for ch in self.children if ch is not None and hasattr(ch, "__aenter__")]):
            await _

    async def __aexit__(self, *args, **kwargs):
        for _ in asyncio.as_completed([ch.__aexit__(self) for ch in self.children if ch is not None and hasattr(ch, "__aexit__")]):
            await _
