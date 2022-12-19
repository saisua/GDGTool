from logging import exception
from re import L
import cython
import asyncio
import traceback
from typing import *
from itertools import chain
from inspect import iscoroutinefunction
from multiprocessing import Process, Manager
from multiprocessing.managers import ListProxy

from API.Crawler import Crawler

class Live_slave(Crawler):
    slave_local_results: list
    slave_queue: list
    _slave_open: cython.bint

    url_tracking_dict: dict
    
    def __init__(self, *args, **kwargs):
        self.slave_local_results = list()
        self.url_tracking_dict = dict()

        Crawler.__init__(self, *args, **kwargs)
    
    def exec_code(self, code):
        exec(code)

    def eval_code(self, code):
        print(eval(code))
    
    @staticmethod
    def slave_run(*args, slave_queue, slave_results, **kwargs):
        slave_process = Process(target=Live_slave._slave_target, args=[args, slave_queue, slave_results, kwargs])
        slave_process.start()

        return slave_process

    @staticmethod
    def _slave_target(args, slave_queue, slave_results, kwargs):
        slave = Live_slave(*args, **kwargs)

        loop = asyncio.get_event_loop()
        if(loop.is_running()):
            loop.stop()
            loop = asyncio.new_event_loop()

        loop.run_until_complete(slave._slave_run(slave_queue, slave_results))

    async def _slave_run(self, slave_queue, slave_results):
        print("Slave starting...")
        self._slave_open = True
        self.slave_queue = slave_queue

        try:
            await self.open_crawler()

            while(not self.Crawler_enter):
                await asyncio.sleep(1)

            print(f"Slave started ({len(slave_queue)})")

            while True:
                while(not len(slave_queue)):
                    await asyncio.sleep(3)
                
                func_name, mode, args, kwargs = slave_queue.pop(0)
                print(f"Slave got function \"{func_name}\"")
                if(func_name == "exit"):
                    break
                
                func = self
                for obj_name in func_name.split('.'):
                    print(f"Next: {obj_name}", flush=False)
                    func = getattr(func, obj_name)

                    if(func is None):
                        print(f"Aborted. \"{obj_name}\" not found in \"{func_name}\"")
                        continue
                
                try:
                    if(iscoroutinefunction(func)):
                        print(f"Slave async {func_name}({args}, {kwargs})")
                        res = await func(*args, **kwargs)
                        try:
                            slave_results.append(res)
                        except TypeError:
                            self.slave_local_results.append(res)
                    else:
                        if(mode == "async"):
                            print(f"Slave async {func_name}({args}, {kwargs})")
                            res = await func(*args, **kwargs)
                            try:
                                slave_results.append(res)
                            except TypeError:
                                self.slave_local_results.append(res)
                        elif(mode == "agen"):
                            print(f"Slave agen {func_name}({args}, {kwargs})")
                            results = []
                            async for it in func(*args, **kwargs):
                                results.append(await it)
                            try:
                                slave_results.append(results)
                            except TypeError:
                                self.slave_local_results.append(results)
                        elif(mode == "gen"):
                            print(f"Slave gen {func_name}({args}, {kwargs})")
                            results = []
                            for it in func(*args, **kwargs):
                                results.append(it)
                            try:
                                slave_results.append(results)
                            except TypeError:
                                self.slave_local_results.append(results)
                        else:
                            print(f"Slave {func_name}({args}, {kwargs})")
                            res = func(*args, **kwargs)
                            try:
                                slave_results.append(res)
                            except TypeError:
                                self.slave_local_results.append(res)
                except Exception as err:
                    print(f"[-] {err}")
                    traceback.print_exception(err)
                    self.slave_local_results.append(err)
        except Exception as err:
            print(f"Exitted due to exception {err}")
        finally:
            self._slave_open = False
            await self.close_crawler()

    async def apply_contexts(self, func):
        await func(self.browser.contexts)
        self.slave_local_results.append(f"[+] Applied \"{func.__name__}\" to contexts")

    def print_state(self):
        print("#### Current browser state", flush=False)
        for context in self.browser.contexts:
            print(f"# {context}", flush=False)
            for page in context.pages:
                print(f"# | {page}", flush=False)
        print("####", flush=False)
        print(f"# Queue: {len(self.slave_queue)}")
        for result in self.slave_queue[-10:]:
            print(f"# | {result}", flush=False)
        print("####", flush=False)
        print(f"# Outputs: {len(self.slave_local_results)}")
        for result in self.slave_local_results[-10:]:
            print(f"# | {result}", flush=False)
        print("####")

    async def goto(self, url: str) -> None:
        await self.browser.contexts[0].pages[0].goto(url, wait_until="domcontentloaded")
        self.slave_local_results.append(f"[+] Gone to \"{url}\"")

    async def url_tracking(self, callback=None, new_callback=None):
        if(callback is None):
            print("Launched url change tracking")
        else:
            print("Launched url change tracking with callback")
        while self._slave_open:
            await asyncio.sleep(2)

            for context_index, context in enumerate(self.browser.contexts, start=2):
                context_track: dict = self.url_tracking_dict.get(context)
                if(context_track is None):
                    context_track = self.url_tracking_dict[context] = dict()

                for page in context.pages:
                    page_track: list = context_track.get(page)
                    if(page_track is None):
                        page_track = context_track[page] = [page.url]

                    elif(page_track[-1] != page.url):
                        page_track.append(page.url)

                        if(len(page_track) == 3):
                            page_track.pop(0)
                        elif(new_callback is not None):
                            await new_callback(self, page)
                        

                        if(callback is not None):
                            await callback(self, page)
                await asyncio.sleep(2 / context_index)

class ProxyWrapper:
    attrs: list = []

    def __init__(self, attr=None):
        if(attr is not None):
            self.attrs.clear()
            self.attrs.append(attr)

    def get(self) -> Any:
        attr = '.'.join(self.attrs)
        print(f"[P] Get {attr}")

        prev_len = len(Live_browser.slave_shared_results)
        Live_browser.slave_shared_queue.append(("__getattr__", 0, [attr], {}))

        while(len(Live_browser.slave_shared_results) == prev_len):
            pass

        self.attrs.clear()
        return Live_browser.slave_shared_results[-1]

    def __getattr__(self, attr: str) -> object:
        print(f"[P] Got {attr}")
        self.attrs.append(attr)
        return self

    def __setattr__(self, attr: str, value: Any) -> None:
        attr = '.'.join(chain(self.attrs, [attr]))
        print(f"[P] Set {attr} to {value}")
        Live_browser.slave_shared_queue.append(("__setattr__", 0, [attr, value], {}))
        self.attrs.clear()
        
    def __call__(self, *args, **kwargs):
        print(f"[P] Added {'.'.join(self.attrs)} with ({args}, {kwargs})")
        
        mode = kwargs.pop('run_mode', '')
        Live_browser.slave_shared_queue.append(('.'.join(self.attrs), mode, args, kwargs))
        self.attrs.clear()
        
class Live_browser():
    slave_args: tuple
    slave_kwargs: dict

    slave_process: Process

    _manager: Manager
    
    slave_shared_queue: ListProxy
    slave_shared_results: ListProxy

    def __init__(self, *args, **kwargs):
        Live_browser._manager = Manager()
        Live_browser.slave_shared_queue = Live_browser._manager.list()
        Live_browser.slave_shared_results = Live_browser._manager.list()
        Live_browser.slave_args = args
        Live_browser.slave_kwargs = kwargs

    def __enter__(self, *args, **kwargs):
        Live_browser.slave_process = Live_slave.slave_run(
            *Live_browser.slave_args,
            slave_queue = Live_browser.slave_shared_queue,
            slave_results = Live_browser.slave_shared_results,
            **Live_browser.slave_kwargs
        )
        return self

    def __exit__(self, *args, **kwargs):
        Live_browser.slave_shared_queue.insert(0, ('exit', 0, 0, 0))
        Live_browser.slave_process.join()
        
    def __getattr__(self, attr):
        if(attr == 'wait'):
            return
        
        return ProxyWrapper(attr)

    def open(self):
        self.__enter__()

    def close(self):
        self.__exit__()