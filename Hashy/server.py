import asyncio
import logging
from kademlia.network import Server
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_node():
    server = Server()
    port = int(sys.argv[1])
    await server.listen(port)
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("Stopping server")
    finally:
        server.stop()
        await server.bootstrap([("127.0.0.1", port)])

if __name__ == "__main__":
    print("\033c", end="")
    asyncio.run(run_node())
