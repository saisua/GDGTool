# distutils: language=c++

import asyncio
import behave

import os, sys, re

def dirname(path:str, num:int=1): 
    for _ in range(num): path = os.path.dirname(path)
    print(f"Added path: {path}")
    return path
sys.path.append(dirname(os.path.abspath(__file__), 5))

from src.browser_steps import *

@behave.then("We will setup the plugin \"{plugin}\"")
def setup_plugin(context, plugin):
    imp_plugin = __import__(f"Plugins.{plugin}")

    getattr(imp_plugin, plugin).setup(context.browser)

spaces = "\s+"

@behave.then("We will enable the extension \"{extension}\"")
def enable_extension(context, extension):
    if(not hasattr(context, "browser_kwargs")):
        context.browser_kwargs = {}
        
    context.browser_kwargs[f"use_{re.sub(spaces, '_', extension.strip()).lower()}"] = True