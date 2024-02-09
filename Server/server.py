import logging
import asyncio
import sys

from kademlia.network import Server

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
loop.set_debug(True)

server = Server()
loop.run_until_complete(server.listen(int(sys.argv[1])))

try:
    loop.run_forever()
except KeyboardInterrupt:
    log.debug("Server stopped.")
    pass
finally:
    server.stop()
    loop.close()
