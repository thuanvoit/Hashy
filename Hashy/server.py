import asyncio
import logging
from kademlia.network import Server
import sys

logging.basicConfig(level=logging.INFO)

async def run_node():
    server = Server()
    port = int(sys.argv[1])
    await server.listen(port)
    try:
        # keep the server running
        await asyncio.Future()
    except KeyboardInterrupt:
        print("Stopping server")
    finally:
        server.stop()
        await server.bootstrap([("127.0.0.1", port)])

# run the server
# python server.py <port>

if __name__ == "__main__":
    # clear the screen at run
    print("\033c", end="", flush=True)
    asyncio.run(run_node())
