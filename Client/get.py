import logging
import asyncio
from math import ceil
import sys
import os
from PIL import Image
import io
import json
from kademlia.network import Server

# handler = logging.StreamHandler()
# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# log = logging.getLogger('kademlia')
# log.addHandler(handler)
# log.setLevel(logging.DEBUG)


async def run():
    server = Server()
    await server.listen(8469)
    bootstrap_node = ('127.0.0.1', 8468)
    await server.bootstrap([bootstrap_node])

    while True:

        filename = input("Enter the filename to download [q to quit]: ")

        if filename.lower() == "q":
            break

        chunk_len = await server.get(filename)

        if chunk_len == None:
            print(f"File {filename} not found")
            continue

        fileext = await server.get(f"{filename}_ext")

        chunks = []

        for i in range(chunk_len):
            print(f"Getting chunk {i}/{chunk_len}")
            print("\033c", end="")
            chunk = await server.get(f"{filename}_{i}")
            chunks.append(chunk)

        joined = join_byte_chunks(chunks)
        file_saver(joined, filename, fileext)

    server.stop()


def img_decoder(data):
    '''
    Decode image from bytes 
    return PIL.Image object
    '''
    img = Image.open(io.BytesIO(data))
    return img


def join_byte_chunks(chunks):
    # Concatenate all the byte string chunks
    joined_bytes = b''.join(chunks)
    return joined_bytes


def file_saver(data, filename, fileext):
    '''
    Create folder name download in Client directory if not exists
    Save file to download folder

    @param data: bytes - image in bytes
    @param filename: str - name of file without extension
    '''
    if not os.path.exists("download"):
        os.makedirs("download")
    img_decoder(data).save(f"download/{filename}.{fileext}")
    print(f"File saved as {filename}.{fileext}")
    return


if __name__ == "__main__":
    asyncio.run(run())
