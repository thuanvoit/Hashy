import logging
import asyncio
import sys

from kademlia.network import Server

# Set up logging
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

# Function to start the server and bootstrap it to the provided nodes


async def start_server_and_bootstrap(port, bootstrap_nodes):
    server = Server()
    await server.listen(port)
    await server.bootstrap(bootstrap_nodes)
    return server

# Define the bootstrap nodes (can be multiple)
bootstrap_nodes = [("127.0.0.1", int(sys.argv[1]))]  # Example bootstrap node

# Get the port from the command-line arguments
if len(sys.argv) < 2:
    print("Usage: python your_script.py <port>")
    sys.exit(1)

port = int(sys.argv[2])

# Create and run the event loop


async def main():
    server = await start_server_and_bootstrap(port, bootstrap_nodes)
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        log.debug("Server stopped.")
    finally:
        server.stop()

# Run the main coroutine
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
