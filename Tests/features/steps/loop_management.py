# distutils: language=c++

import asyncio
import behave

@behave.when("We get the event loop")
def get_event_loop(context):
    context.loop = asyncio.get_event_loop()

    assert context.loop is not None
