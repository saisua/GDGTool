# distutils: language=c++

import asyncio
from distutils.command.install_egg_info import to_filename
import os
import pickle, json
import re
from shutil import ExecError
from typing import Iterable

def default(obj):
    if(isinstance(obj, set)):
        return list(obj)
    if(hasattr(obj, "_getvalue")):
        return obj._getvalue()

    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)

class Storage:
    path:str = "Data/"

    storage_library = json

    data_repr:dict = {}
    file_cache:dict = {}
    data:dict = {}

    to_filename_re:re.Pattern = re.compile(r"[^\w\d_\-.]+")

    def __init__(self, remove_old_data:bool=False) -> None:
        if(not remove_old_data):
            self.fill_file_cache()
        try:
            os.mkdir(f"{self.path}")
        except FileExistsError:
            pass
        setattr(self, "Storage_init", True)

    async def add_data(self, key:str, reg:tuple) -> None:
        data_list = self.data.get(key)

        if(data_list is None):
            self.data[key] = [reg]
        else:
            data_list.append(reg)
            
            if(len(data_list) == 10):
                asyncio.create_task(self.store_data(key, data_list.copy()))

                data_list.clear()

    async def update_data(self, key:str, reg:Iterable[tuple]) -> None:
        data_list = self.data.get(key)

        if(data_list is None):
            if(len(reg) > 10):
                asyncio.create_task(self.store_data(key, reg))
            else:
                self.data[key] = list(reg)
        else:
            data_list.extend(reg)
            
            if(len(data_list) == 10):
                asyncio.create_task(self.store_data(key, data_list.copy()))

                data_list.clear()            
    
    async def store_data(self, key, data:list) -> None:
        key = self.to_filename_re.sub('_', key.strip('/ '))
        file_list = self.file_cache.get(key)
        if(file_list is None):
            # May be better to check with an if statement
            try:
                os.mkdir(f"{self.path}/{key}")
            except FileExistsError:
                pass
            file_list = self.file_cache[key] = set()

        for filename, content in data:
            filename = self.to_filename_re.sub('_', filename.strip('/ '))
            if(filename not in file_list):
                file_list.add(filename)
                with open(f"{self.path}/{key}/{filename}.json", "w") as file:
                    self.storage_library.dump(content, file, default=default)
            else:
                with open(f"{self.path}/{key}/{filename}.json", "a") as file:
                    self.storage_library.dump(content, file, default=default)

    async def dump_all_data(self) -> None:
        for _ in asyncio.as_completed([self.store_data(key, data) for key, data in self.data.items()]):
            await _

        self.data.clear()

    def load_data(self, domain, file) -> list:
        objs = []
        with open(f"{self.path}/{domain}/{file}.json", "r") as file:
            while True:
                try:
                    objs.append(self.storage_library.load(file))
                except Exception:
                    break
        return objs

    def fill_file_cache(self) -> None:
        folders_iter = os.walk(self.path)

        for folder in next(folders_iter)[1]:
            self.file_cache[folder] = set(next(folders_iter)[2])