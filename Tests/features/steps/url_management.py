import behave
import re

@behave.given("We want to {run} \"{url:S}\"")
def store_url(context, run, url):
    assert run.lower() in {"open", "crawl"}
    context.url = url

@behave.given("We want to {run} urls")
def store_url(context, run):
    context.urls = [x["url"] for x in context.table]

@behave.when("The url is valid")
def validate_url_valid(context):
    assert hasattr(context, "url"), "There was no single url mentioned. Did you mean \"The urls are valid\"?"
    assert re.match(r'^https?:\/\/\w+(\.\w+)+(\/.*)?', context.url) is not None

@behave.when("The urls are valid")
def validate_url_valid(context):
    assert hasattr(context, "urls"), "There was no single url mentioned. Did you add \"The url is valid\"?"
    
    for url in context.urls:
        print(url)
        assert re.match(r'^https?:\/\/\w+(\.\w+)+(\/.*)?', url) is not None