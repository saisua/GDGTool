# distutils: language=c++

import asyncio
import behave

@behave.given("We want to use \"{data}\"")
def then_open_browser(context, data):
    context.data = data

@behave.then("We will execute the endscript \"{endscript}\"")
def then_open_url(context, endscript):
    imp_endscript = __import__(f"EndScripts.{endscript}")

    context.loop.run_until_complete(getattr(imp_endscript, endscript).main(

    ))