# distutils: language=c++

import cython
import asyncio
import os
import re

import argparse
    
from API.Live import Live_browser

from EndScripts.Keywords import get_keywords
from EndScripts.Summary import summarize_one
from EndScripts.Information_graph import generate_one_graph

HOME = 'https://duckduckgo.com'

shared_objects = {"block pages": True}

async def manage_new_page(page):
    if(shared_objects.get("block pages", False)):
        print("Blocked the creation of a new page", flush=False)
        await page.close()

async def manage_contexts(contexts):
    print(f"Setting up {len(contexts)} contexts...", flush=False)
    for context in contexts:
        context.on("page", manage_new_page)
    print("Contexts set up")


def change_block(event, window, browser:Live_browser):
    global shared_objects

    if(shared_objects.get("block pages")):
        window["block status"].update("Page opening: Unblocked")
        shared_objects["block pages"] = False
    else:
        window["block status"].update("Page opening: Blocked")
        shared_objects["block pages"] = True

async def summarize(event, window, browser:Live_browser):
    browser.get("browser.contexts")
    await browser.wait_until_done()

    context = browser.slave_shared_results[-1][0]
    page = context.pages[0]

    browser.add_command("get_text", page=page, mode="async")
    text = await browser.wait_until_done()

    if(type(text) == str):
        summary = summarize_one(text)
        print()
    #browser.get_text()

async def keywords(event, window, browser:Live_browser):
    print("Keywords request contexts")
    browser.get("browser.contexts")
    context = await browser.wait_until_done()

    print(f"Keywords get page {context=}")
    if(len(context) == 0 or len(context[0].pages) == 0):
        return
    
    page = context[0].pages[0]

    print("Keywords request text")
    browser.add_command("get_text", page=page, mode="async")
    text = await browser.wait_until_done()

    if(type(text) == str):
        result_keywords = get_keywords([text])
        
        window["tool"].update(f"Keywords: {result_keywords}")

async def open_test_page(event, window, browser:Live_browser):
    test_page = "https://en.wikipedia.org/wiki/Resolution_Guyot"

    browser.add_command("open_websites", websites={test_page,}, mode="agen")

async def test(event, window, browser:Live_browser):
    browser.get("browser.contexts")
    context = (await browser.wait_until_done())[0]
    
    page = context.pages[0]

    browser.add_command("get_text", page=page, mode="async")
    text = await browser.wait_until_done()

    if(type(text) == str):
        graph = generate_one_graph(text)
        print()
        import pickle as pkl
        with open("test.graph", 'wb+') as f:
            pkl.dump(graph, f)
    #browser.get_text()

def parse_args(args: list=None, previous_args: dict=None, *, _rescan: bool=False):
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-b", "--browser", 
        help="The browser to be used",
        type=str,
        default="firefox",
        choices=["firefox", "chromium"]
    )
    parser.add_argument("-S", "--session", 
        help="Load the session and store it when finished", 
        type=str,
    )
    parser.add_argument("-ls", "--load_session",
        help="Load the given session",
        default=True,
        action='store_const',
        const=False,
    )
    parser.add_argument("-ss", "--store_session",
        help="Store the current session",
        default=True,
        action='store_const',
        const=False,
    )
    parser.add_argument("-C", "--configuration",
        help="Load the args in a configuration file in Settings/Configuration",
        type=str,
    )
    parser.add_argument("-Ust", "--use_storage",
        help="Whether to use the Storage component",
        default=False,
        action='store_true',
    )
    parser.add_argument("-Use", "--use_session",
        help="Whether to use the Session component",
        default=False,
        action='store_true',
    )
    parser.add_argument("--persistent", 
        help="If the browser should be persistent and keep cookies [experimental]",
        default=False,
        action='store_true',
    )
    parser.add_argument("-v", "--verbose", 
        help="Output verbose information",
        default=False,
        action='store_true',
    )
    parser.add_argument("-A", "--addons", 
        help="A substring or regular expression to install all addons in Settings/Addons that match the given pattern",
        type=str,
        default="search",
    )
    parser.add_argument('websites', metavar='W', type=str, nargs='*',
        help='The websites to open',
        default=[HOME]
    )
    
    parsed_args = parser.parse_args(args, previous_args)

    if(parsed_args.configuration and not _rescan):
        config_path = os.path.join('.', "Settings", "Configurations", parsed_args.configuration)

        print(f"Using configuration {config_path}")
        if(os.path.exists(config_path) and os.path.isfile(config_path)):
            config_args: str
            with open(config_path, 'r') as f:
                config_args = f.read()
            return parse_args(filter(None, re.split(r'\s+', config_args)), parsed_args, _rescan=True)
        else:
            print(f"[-] Wrong config file. \"{config_path}\" does not exist or it is not a file")

    return parsed_args

def apply_args(parsed_args):
    if(parsed_args.session):
        parsed_args.use_session = True
        if(parsed_args.load_session or parsed_args.store_session):
            parsed_args.use_storage = True

    return parsed_args

async def main():
    cmd_args = apply_args(parse_args())

    gui_browser = Live_browser(
        use_storage=cmd_args.use_storage,
        use_session=cmd_args.use_session,

        headless=False,
        browser_name=cmd_args.browser,
        browser_persistent=cmd_args.persistent,
        verbose=cmd_args.verbose,
        install_addons=cmd_args.addons,

        session_name=cmd_args.session,
        autoload_session=cmd_args.load_session,
        autostore_session=cmd_args.store_session,
        fall_missing_session=cmd_args.websites,

        slave_shared_objects=shared_objects,
    )

    if(not cmd_args.session or not cmd_args.load_session):
        gui_browser.add_command("open_websites", websites=set(cmd_args.websites), mode="agen")
    gui_browser.add_command("apply_contexts", manage_contexts, mode="async")

    buttons = {
        "Block open websites": change_block,
        "Get website keywords": keywords,
        "Open test website": open_test_page,
        #"Test": test,
    }
    texts = {
        "block status": "Page opening: Blocked",
        "tool": "",
    }

    gui_browser.open()
    await gui_browser.loop(control_buttons=buttons, texts=texts)
    gui_browser.close()

if(__name__ == "__main__"):
    asyncio.run(main())
