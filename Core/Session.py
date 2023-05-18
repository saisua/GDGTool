# distutils: language=c++
import cython
import os

from typing import *

import pickle as pkl

class Session:
    session_parent:object
    session_name:str

    session_storage_path:str

    autostore_session:cython.bint
    autoload_session:cython.bint

    session_contexts:list
    Session_init:cython.bint

    _fall_missing_session:set
    
    def __init__(self, parent, *args, **kwargs):
        print(f"{' '*kwargs.get('verbose_depth', 0)}Initializing Session")

        self.session_parent = parent
        self.session_name = kwargs.pop("session_name", "session")
        self.autoload_session = kwargs.pop("autoload_session", False)
        self.autostore_session = kwargs.pop("autostore_session", False)

        self.session_storage_path = kwargs.pop('session_storage_path', 'Settings/Sessions').rstrip('/')

        self._fall_missing_session = set(kwargs.pop('fall_missing_session', set()))

        self.session_contexts = kwargs.get("contexts", [])
        self.Session_init = True

    async def __aenter__(self, *args, step:cython.bint=1, **kwargs):
        if(not self.Session_init): return
        if(step != 1): return

        if(not os.path.exists(self.session_storage_path)):
            print(f"Session {self.session_name} did not exist")
            os.mkdir(self.session_storage_path)
        elif(not os.path.isdir(self.session_storage_path)):
            raise FileExistsError()
        elif(self.autoload_session):
            print(f"Session {self.session_name} exists. Loading session")
            await self._load_session(self.session_name)

    async def __aexit__(self, *args, step:cython.bint=0, **kwargs):
        if(not self.Session_init): return
        if(step != 0): return

        if(self.autostore_session):
            print(f"Storing session {self.session_name}")
            with open(f"{self.session_storage_path}/{self.session_name}.sess", "wb+") as f:
                pkl.dump({
                    page.url 
                        for context in self.session_parent.browser.contexts 
                            for page in context.pages
                }, f)

    async def _load_session(self, session_name:str) -> List[str]:
        session_name = f"{self.session_storage_path}/{self.session_name}.sess"

        if(os.path.exists(session_name)):
            if(not os.path.isfile(session_name)):
                raise FileExistsError()
            websites: set
            with open(session_name, "rb") as f:
                websites = pkl.load(f)

            context = await self.session_parent._new_context()

            async for _ in self.session_parent._open_websites(context, websites):
                await _
        else:
            context = await self.session_parent._new_context()

            async for _ in self.session_parent._open_websites(context, self._fall_missing_session):
                await _