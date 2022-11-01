# distutils: language=c++

import asyncio
from distutils.command.install_egg_info import to_filename
import os
import pickle, json
import cython
import re

from typing import Iterable
from datetime import datetime

def default(obj):
    if(isinstance(obj, set)):
        return list(obj)
    if(hasattr(obj, "_getvalue")):
        return obj._getvalue()

    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)

class Storage:
    storage_base_path:str = "Data/"
    storage_path:str

    storage_library = json
    max_memory_domains:cython.uint

    storage_data_repr:dict = {}
    file_cache:dict = {}
    storage_data:dict = {}

    to_filename_re:re.Pattern = re.compile(r"[^\w\d_\-.]+")

    def __init__(self, *args, remove_old_data:bool=False, folder_name:str=None, max_memory_domains:cython.uint=10, **kwargs) -> None:
        if(not remove_old_data):
            self.fill_file_cache()

        self.storage_path = self.storage_base_path + (folder_name or f"{str(datetime.now()).split('.')[0]}/")
        self.max_memory_domains = max_memory_domains

        setattr(self, "Storage_init", True)

    async def __aenter__(self, *args, **kwargs):
        try:
            os.mkdir(f"{self.storage_base_path}")
        except FileExistsError:
            pass
                
        try:
            os.mkdir(f"{self.storage_path}")
        except FileExistsError:
            pass

    async def __aexit__(self, *args, **kwargs):
        await self.dump_all_data()

    async def add_data(self, key:str, reg:tuple) -> None:
        data_list = self.storage_data.get(key)

        if(data_list is None):
            self.storage_data[key] = [reg]
        else:
            data_list.append(reg)
            
            if(len(data_list) == self.max_memory_domains):
                store_list = data_list.copy()
                data_list.clear()
                asyncio.create_task(self.store_data(key, store_list))


    async def update_data(self, key:str, reg:Iterable[tuple]) -> None:
        data_list = self.storage_data.get(key)

        if(data_list is None):
            if(len(reg) > self.max_memory_domains):
                asyncio.create_task(self.store_data(key, reg))
            else:
                self.storage_data[key] = list(reg)
        else:
            data_list.extend(reg)
            
            if(len(data_list) == self.max_memory_domains):
                store_list = data_list.copy()
                data_list.clear()
                asyncio.create_task(self.store_data(key, store_list))       
    
    async def store_data(self, key: str, data: list, *, force: cython.bint = False) -> None:
        key = self.to_filename_re.sub('_', key.strip('/ '))
        file_list: list = self.file_cache.get(key)
        if(file_list is None):
            # May be better to check with an if statement
            try:
                os.mkdir(f"{self.storage_path}/{key}")
            except FileExistsError:
                pass
            file_list = self.file_cache[key] = set()

        store_data: list = data.copy()
        data.clear()
        filename: str
        content: dict
        for filename, content in store_data:
            if(not force and content.get('locks', 0) != 0):
                data.append((filename, content))
                continue
            filename = self.to_filename_re.sub('_', filename.strip('/ '))
            if(filename not in file_list):
                file_list.add(filename)
                with open(f"{self.storage_path}/{key}/{filename}.json", "w") as file:
                    self.storage_library.dump(content, file, default=default, ensure_ascii=False)
            else:
                with open(f"{self.storage_path}/{key}/{filename}.json", "a") as file:
                    self.storage_library.dump(content, file, default=default, ensure_ascii=False)

        

    async def dump_all_data(self) -> None:
        all_storage_data = list(self.storage_data.items())
        self.storage_data.clear()

        for _ in asyncio.as_completed([self.store_data(key, data, force=True) for key, data in all_storage_data]):
            await _

    def load_data(self, domain, file) -> list:
        objs = []
        with open(f"{self.storage_path}/{domain}/{file}.json", "r") as file:
            while True:
                try:
                    objs.append(self.storage_library.load(file))
                except Exception:
                    break
        return objs

    def fill_file_cache(self) -> None:
        folders_iter = os.walk(self.storage_path)

        for folder in next(folders_iter)[1]:
            self.file_cache[folder] = set(next(folders_iter)[2])