from typing import Pattern
from pathlib import Path
import re
import json

def load_data(
        folder: str,
        storage_base_path: str='.',
        folder_regex: Pattern= '.*',
        file_regex: Pattern = '.*',
        *args,
        storage_library: object = json,
        forced_extension: str = ".json",
        is_binary: bool = False,
        **kwargs,
    ):
    """Get the run folder for {Data_path}/{folder} and walk the directory tree 
       loading the directories that match the folder_regex and then the file_regex

    Args:
        folder (str): The folder (stored execution folder)
        folder_regex (Pattern): The regex that matches what folders will be loaded
        file_regex (Pattern): The regex that matches what JSON files will be loaded
    """
    root_scan_path: Path = Path(storage_base_path, folder)
    if(not root_scan_path.exists() or not root_scan_path.is_dir()):
        return {}, folder

    if(type(folder_regex) == str):
        folder_regex = re.compile(folder_regex)
    if(type(file_regex) == str):
        file_regex = re.compile(f"{file_regex}")

    ext_len = len(forced_extension)

    root_data = {}
    scan_paths = [(root_data, root_scan_path)]
    while len(scan_paths):
        data_dict, scan_path = scan_paths.pop(0)

        for path in scan_path.iterdir():
            spath = path.name
            if(path.is_dir()):
                if(folder_regex.match(spath)):
                    new_data_dict = dict()
                    data_dict[f"{spath}/"] = new_data_dict
                    scan_paths.append((new_data_dict, path))
            elif(path.is_file()):
                if(spath.endswith(forced_extension) and file_regex.match(spath)):
                    with open(str(path), 'rb' if is_binary else 'r', encoding='utf-8') as f:
                        data_dict[spath[:-ext_len]] = storage_library.load(f)

    return root_data, folder
