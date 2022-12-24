import asyncio

children = []
class Children:
    def __init__(self, children_: tuple):
        children.extend(children_)

    def __getattr__(self, attr: str):
        #print(f"Accessing {attr}", flush=False)
        for child in children:
            if(child is not None and hasattr(child, attr)):
                return getattr(child, attr)
            #elif(child is not None):
                #print(f" {child.__class__.__name__} has no \"{attr}\"", flush=False)

    async def __aenter__(self, *args, **kwargs):
        for _ in asyncio.as_completed([ch.__aenter__(self) for ch in children if ch is not None and hasattr(ch, "__aenter__")]):
            await _

    async def __aexit__(self, *args, **kwargs):
        for _ in asyncio.as_completed([ch.__aexit__(self) for ch in children if ch is not None and hasattr(ch, "__aexit__")]):
            await _
