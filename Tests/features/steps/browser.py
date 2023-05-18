# distutils: language=c++

import asyncio
import behave

from src.browser_steps import *

@behave.then("A new browser will be created")
def then_open_browser(context):
    context.loop.run_until_complete(open_browser(context))
    
    assert hasattr(context, 'browser')
    assert context.browser is not None
    assert context.browser.browser is not None

@behave.then("The {browser} will open the url")
def then_open_url(context, browser):
    context.loop.run_until_complete(open_url(context))

@behave.then("The {browser} will open the urls")
def then_open_urls(context, browser):
    context.loop.run_until_complete(open_urls(context))

@behave.then("The {browser} will wait to be closed")
def then_wait_closed(context, browser):
    try:
        context.loop.run_until_complete(wait_until_closed(context))
    except KeyboardInterrupt:
        print("Interrupting...")

@behave.then("The {browser} will close")
def then_close_browser(context, browser):
    context.loop.run_until_complete(close_browser(context))