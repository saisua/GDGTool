import json
import os
from typing import Union, List

def store_data(
        obj: Union[dict, List[dict]],
        path: str,
        *,
        storage_library: object = json,
        forced_extension: str = ".json",
        is_binary: bool = False
    ):
    store_q = []

    start_path = f"{path.rstrip('/')}/"

    if(type(obj) == dict):
        store_q.append((start_path, obj))
    elif(type(obj) == list):
        store_q.extend(((start_path, o) for o in obj))
    else:
        raise ValueError("Unknown type for 'obj' parameter. It must be a list or a dict.")

    while(len(store_q)):
        path, obj = store_q.pop()

        for key, value in obj.items():
            if(key.endswith('/')):
                store_q.append((f"{path}/{key.strip('/')}", value))
            else:
                if(not os.path.exists(path)):
                    os.makedirs(path)
                
                with open(f"{path}/{key.strip('/')}{forced_extension}", 'wb+' if is_binary else 'w+') as f:
                    storage_library.dump(value, f)