from logging import exception
from re import L
import cython
import asyncio
import traceback
from typing import *
from itertools import chain
from inspect import iscoroutinefunction
from threading import Thread, Lock

from API.Crawler import Crawler

from Extensions.Control_GUI import Control_GUI

class Browser_slave(Crawler):
    slave_local_results: list
    slave_results: list
    slave_queue: list

    slave_queue_lock: Lock
    slave_results_lock: Lock

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
    def _slave_target(args, slave_queue, slave_results, slave_queue_lock, slave_results_lock, kwargs):
        slave = Browser_slave(*args, **kwargs)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        
        if(loop.is_running()):
            loop.stop()
            loop = asyncio.new_event_loop()

        loop.run_until_complete(slave._slave_run(slave_queue, slave_results, slave_queue_lock, slave_results_lock))

    async def _slave_run(self, slave_queue, slave_results, slave_queue_lock, slave_results_lock):
        print("Slave starting...")
        self._slave_open = True
        self.slave_queue = slave_queue
        self.slave_results = slave_results
        self.slave_queue_lock = slave_queue_lock
        self.slave_results_lock = slave_results_lock

        try:
            await self.open_crawler()

            while(not self.Crawler_enter):
                await asyncio.sleep(1)

            print(f"Slave started ({len(slave_queue)})")

            while True:
                if(not len(slave_queue)):
                    while True:
                        if(len(slave_queue)):
                            break
                        await asyncio.sleep(3)
                        print("Waiting", end='\r')
                print()
                
                with slave_queue_lock:
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
                        try:
                            res = await func(*args, **kwargs)
                        except TypeError:
                            res = await func(self, *args, **kwargs)
                            
                        try:
                            with slave_results_lock:
                                slave_results.append(res)
                        except TypeError:
                            self.slave_local_results.append(res)
                    else:
                        if(mode == "async"):
                            print(f"Slave async {func_name}({args}, {kwargs})")
                            try:
                                res = await func(*args, **kwargs)
                            except TypeError:
                                res = await func(self, *args, **kwargs)

                            try:
                                with slave_results_lock:
                                    slave_results.append(res)
                            except TypeError:
                                self.slave_local_results.append(res)
                        elif(mode == "agen"):
                            print(f"Slave agen {func_name}({args}, {kwargs})")
                            results = []
                            try:
                                async for it in func(*args, **kwargs):
                                    results.append(await it)
                            except TypeError:
                                async for it in func(self, *args, **kwargs):
                                    results.append(await it)
                            
                            try:
                                with slave_results_lock:
                                    slave_results.append(results)
                            except TypeError:
                                self.slave_local_results.append(results)
                        elif(mode == "gen"):
                            print(f"Slave gen {func_name}({args}, {kwargs})")
                            results = []
                            try:
                                for it in func(*args, **kwargs):
                                    results.append(it)
                            except TypeError:
                                for it in func(self, *args, **kwargs):
                                    results.append(it)

                            try:
                                with slave_results_lock:
                                    slave_results.append(results)
                            except TypeError:
                                self.slave_local_results.append(results)
                        else:
                            print(f"Slave {func_name}({args}, {kwargs})")
                            try:
                                res = func(*args, **kwargs)
                            except TypeError:
                                res = func(self, *args, **kwargs)

                            try:
                                with slave_results_lock:
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
        with self.slave_queue_lock:
            print(f"# Queue: {len(self.slave_queue)}")
            for result in self.slave_queue[-10:]:
                print(f"# | {result}", flush=False)
        print("####", flush=False)
        print(f"# Outputs: {len(self.slave_local_results)}")
        for result in self.slave_local_results[-10:]:
            print(f"# | {result}", flush=False)
        print("####")

    def get(self, variable: str, *args, **kwargs):
        obj = self
        for obj_name in variable.split('.'):
            print(f"Next: {obj_name}", flush=False)
            obj = getattr(obj, obj_name)

            if(obj is None):
                print(f"Aborted. \"{obj_name}\" not found in \"{variable}\"")
                continue

        return obj

    async def goto(self, url: str, *args, **kwargs) -> None:
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

class Live_browser(Control_GUI):
    slave_args: tuple
    slave_kwargs: dict

    slave_thread: Thread

    slave_shared_queue: list
    slave_shared_results: list

    slave_shared_queue_lock: Lock
    slave_shared_results_lock: Lock

    slave_shared_objects: dict

    def __init__(self, *args, **kwargs):
        self.slave_shared_queue = list()
        self.slave_shared_results = list()
        self.slave_shared_queue_lock = Lock()
        self.slave_shared_results_lock = Lock()
        self.slave_shared_objects = kwargs.get("slave_shared_objects", dict())

        self.slave_args = args
        self.slave_kwargs = kwargs

    def __enter__(self, *args, **kwargs):
        self.slave_thread = Live_browser._create_slave(
            *self.slave_args,
            slave_queue = self.slave_shared_queue,
            slave_results = self.slave_shared_results,
            slave_queue_lock = self.slave_shared_queue_lock,
            slave_results_lock = self.slave_shared_results_lock,
            **self.slave_kwargs
        )

    def __exit__(self, *args, **kwargs):
        self.slave_shared_queue.insert(0, ('exit', 0, 0, 0))
        self.slave_thread.join()
    
    def open(self, *args, **kwargs):
        self.__enter__(*args, **kwargs)

    def close(self):
        self.__exit__()

    def add_command(self, command: str, *args, mode: str='', **kwargs):
        print(f"Added command \"{command}\"")
        with self.slave_shared_queue_lock:
            self.slave_shared_queue.append((command, mode, args, kwargs))

    def get(self, variable):
        print(f"Get \"{variable}\"")
        with self.slave_shared_queue_lock:
            self.slave_shared_queue.append(("get", None, [variable], {}))

    async def wait_until_done(self, expected_delay: float = 0.25):
        expected_results = len(self.slave_shared_results) + len(self.slave_shared_queue)
        last_remaining = len(self.slave_shared_queue)
        same_remaining_times = 0
        while(last_remaining):
            await asyncio.sleep(0.25)
            
            new_remaining = len(self.slave_shared_queue)
            if(last_remaining != new_remaining):
                last_remaining = new_remaining
                same_remaining_times = 0
            else:
                same_remaining_times += 1
                if(same_remaining_times >= 20):
                    with self.slave_shared_queue_lock:
                        last_remaining = len(self.slave_shared_queue)
                        if(last_remaining != 0):
                            self.slave_shared_queue.pop(0)
                    same_remaining_times = 0

        # Just in case there is a race condition, keep 1 as margin. 
        # It is suposed to be 0
        if(abs(len(self.slave_shared_results) - expected_results) == 1):
            await asyncio.sleep(expected_delay)

        last_result = None
        with self.slave_shared_results_lock:
            last_result = self.slave_shared_results[-1]

        return last_result

    @staticmethod
    def _create_slave(*args, slave_queue, slave_results, slave_queue_lock, slave_results_lock, **kwargs):
        slave_process = Thread(target=Browser_slave._slave_target, args=[args, slave_queue, slave_results, slave_queue_lock, slave_results_lock, kwargs])
        slave_process.start()

        return slave_process