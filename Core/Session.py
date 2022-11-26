# distutils: language=c++
import cython

from typing import *


class Session:
    session_child:object
    session_name:str
    autosave_session:cython.bint

    session_contexts:list
    Session_init:cython.bint

    

    def __init__(self, child, *args, **kwargs):
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Session")

        self.session_child = child
        self.session_name = kwargs.pop("name", "session")
        self.autosave_session = kwargs.pop("autosave_session", False)

        self.session_contexts = kwargs.get("contexts", [])
        self.Session_init = True

    async def __aenter__(self, *args, **kwargs):
        if(not self.Session_init): return

    async def __aexit__(self, *args, **kwargs):
        if(not self.Session_init): return

        if(self.autosave_session):
            # Might be best to store too the visited_urls if it exists
            await self.session_child.update_data("Session", [
                    (f"{self.session_name}.{cnum}", {page.url for page in context.pages})
                        for cnum, context in enumerate(self.session_child.browser.contexts)
            ])

    async def _load_session(self, session_name:str) -> List[str]:
        return self.session_child.load_data("Session", session_name)