from logging import exception
from re import L
import cython
import asyncio
from inspect import iscoroutinefunction
from multiprocessing import Process, Manager
from multiprocessing.managers import ListProxy

from API.Crawler import Crawler

class Live_slave(Crawler):
    def __init__(self, *args, **kwargs):
        Crawler.__init__(self, *args, **kwargs)
    
    def exec_code(self, code):
        exec(code)

    def eval_code(self, code):
        print(eval(code))
    
    @staticmethod
    def slave_run(*args, slave_queue, **kwargs):
        slave_process = Process(target=Live_slave._slave_target, args=[args, slave_queue, kwargs])
        slave_process.start()

        return slave_process

    @staticmethod
    def _slave_target(args, slave_queue, kwargs):
        slave = Live_slave(*args, **kwargs)

        loop = asyncio.get_event_loop()
        if(loop.is_running()):
            loop.stop()
            loop = asyncio.new_event_loop()

        loop.run_until_complete(slave._slave_run(slave_queue))

    async def _slave_run(self, slave_queue):
        print("Slave starting...")
        
        try:
            await self.open_crawler()

            print(f"Slave started ({len(slave_queue)})")

            while True:
                while(not len(slave_queue)):
                    print("[W]", end='\r')
                    await asyncio.sleep(3)
                
                func_name, mode, args, kwargs = slave_queue.pop(0)
                print(f"Slave got function \"{func_name}\"")
                if(func_name == "exit"):
                    break

                func = getattr(self, func_name)
                try:
                    if(iscoroutinefunction(func)):
                        print(f"Slave async {func_name}({args}, {kwargs})")
                        await func(*args, **kwargs)
                    else:
                        if(mode == "async"):
                            print(f"Slave async {func_name}({args}, {kwargs})")
                            await func(*args, **kwargs)
                        elif(mode == "agen"):
                            print(f"Slave agen {func_name}({args}, {kwargs})")
                            async for it in func(*args, **kwargs):
                                await it
                        elif(mode == "gen"):
                            print(f"Slave gen {func_name}({args}, {kwargs})")
                            for it in func(*args, **kwargs):
                                pass
                        else:
                            print(f"Slave {func_name}({args}, {kwargs})")
                            func(*args, **kwargs)
                except Exception as err:
                    print(f"[-] {err}")
        except Exception as err:
            print(f"Exitted due to exception {err}")
        finally:
            await self.close_crawler()
        
class Live_browser():
    slave_args: tuple
    slave_kwargs: dict

    slave_process: Process

    _manager: Manager
    
    slave_shared_queue: ListProxy

    def __init__(self, *args, **kwargs):
        Live_browser._manager = Manager()
        Live_browser.slave_shared_queue = Live_browser._manager.list()
        Live_browser.slave_args = args
        Live_browser.slave_kwargs = kwargs

    def __enter__(self, *args, **kwargs):
        Live_browser.slave_process = Live_slave.slave_run(
            *Live_browser.slave_args,
            slave_queue = Live_browser.slave_shared_queue,
            **Live_browser.slave_kwargs
        )
        return self

    def __exit__(self, *args, **kwargs):
        Live_browser.slave_shared_queue.insert(0, ('exit', 0, 0, 0))
        Live_browser.slave_process.join()
        
    def __getattr__(self, attr):
        if(attr == 'wait'):
            return
            
        def _qadd(*args, **kwargs):
            print(f"Added {attr} with ({args}, {kwargs})")
            mode = kwargs.pop('run_mode', '')
            Live_browser.slave_shared_queue.append((attr, mode, args, kwargs))
        return _qadd

    def open(self):
        self.__enter__()

    def close(self):
        self.__exit__()