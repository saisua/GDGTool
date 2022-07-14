import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core.Distributed import Server

async def basic_distributed_server():
    async with Server(headless=False, use_rotating_proxies=False, use_resources=False) as server:
        print(dir(server))
        server._register("crawler")
        print("\nServer ready")
        #server.start()
        
if(__name__ == "__main__"):
    try:
        asyncio.run(basic_distributed_server())
    except ValueError:
        pass