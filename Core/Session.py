# distutils: language=c++

from typing import *


class Session:
    child:object
    name:str
    autosave_session:bool = False

    contexts:list

    def __init__(self, child, *args, **kwargs):
        self.child = child
        self.name = kwargs.pop("name", "session")
        self.autosave_session = kwargs.pop("autosave_session", False)

        self.contexts = kwargs.get("contexts", [])
        setattr(self, "Session_init", True)

    async def __aenter__(self):
        if(not hasattr(self, "Session_init")): return

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if(not hasattr(self, "Session_init")): return

        if(self.autosave_session):
            # Might be best to store too the visited_urls if it exists
            await self.child.update_data("Session", [
                    (f"{self.name}.{cnum}", {page.url for page in context.pages})
                        for cnum, context in enumerate(self.child.browser.contexts)
            ])

    async def _load_session(self, session_name:str) -> List[str]:
        return self.child.load_data("Session", session_name)