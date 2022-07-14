# distutils: language=c++

import asyncio
import behave

from src.crawler_steps import *

@behave.then("We will setup a search for \"{search_str}\"")
def given_search(context, search_str):
    context.loop.run_until_complete(search(context, search_str))

@behave.then("We will setup a search for \"{search_str}\" in {domain}")
def given_search(context, search_str, domain):
    context.loop.run_until_complete(search(context, search_str, domain))

@behave.then("A new crawler will be created")
def then_open_browser(context):
    context.loop.run_until_complete(open_crawler(context))

@behave.then("The {crawler} will add the urls")
def then_add_urls(context, crawler):
    context.loop.run_until_complete(add_urls(context))

@behave.then("The {crawler} will crawl")
def then_crawl(context, crawler):
    context.loop.run_until_complete(crawl(context))

@behave.then("The {crawler} will crawl {levels:d} levels")
def then_crawl(context, crawler, levels):
    context.loop.run_until_complete(crawl(context, levels=levels))

args = {
    "tabs":"max_tabs", "tab":"max_tabs",
    "contexts":"num_contexts", "browsers":"num_contexts",
    "context":"num_contexts", "browser":"num_contexts"
}

@behave.then("The {crawler} will crawl {levels:d} levels with {arg1:d} {arg1name:S}")
def then_crawl(context, crawler, levels, arg1, arg1name):
    context.loop.run_until_complete(crawl(context, levels=levels, **{
        args[arg1name]:arg1
    }))

@behave.then("The {crawler} will crawl {levels:d} levels with {arg1:d} {arg1name:S} and {arg2:d} {arg2name:S}")
def then_crawl(context, crawler, levels, arg1, arg1name, arg2, arg2name):
    context.loop.run_until_complete(crawl(context, levels=levels, **{
        args[arg1name]:arg1,
        args[arg2name]:arg2
    }))

@behave.then("The {crawler} will crawl with {arg1:d} {arg1name:S}")
def then_crawl(context, crawler, arg1, arg1name):
    context.loop.run_until_complete(crawl(context, **{
        args[arg1name]:arg1
    }))

@behave.then("The {crawler} will crawl with {arg1:d} {arg1name:S} and {arg2:d} {arg2name:S}")
def then_crawl(context, crawler, arg1, arg1name, arg2, arg2name):
    context.loop.run_until_complete(crawl(context, **{
        args[arg1name]:arg1,
        args[arg2name]:arg2
    }))