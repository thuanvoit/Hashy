import logging
import asyncio
from math import ceil
import sys
import os
from PIL import Image
import io
import json
from kademlia.network import Server
import re
import socket
from contextlib import closing


async def run():
    server = Server()
    # Start the server on the specified port
    await server.listen(int(sys.argv[2]))
    # connect to the server port
    bootstrap_node = ('127.0.0.1', int(sys.argv[1]))
    await server.bootstrap([bootstrap_node])

    while True:
        file_path = input(
            "Enter the file path or key:value pair, [q to quit]: ")

        if file_path.lower() == "q":
            server.stop()
            break

        # sometimes file_path has '' around it
        if file_path.startswith("'") and file_path.endswith("'") \
                or file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]

        print(os.path.isfile(file_path))
        if os.path.isfile(file_path):  # Check if input is a file
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                # extract file name from file path without extension
                file_name = re.search(
                    r"([a-zA-Z0-9\s_\\.\-\(\):])+(.jpg|.jpeg|.png|.gif)$", file_path)

                filename = file_name.group(0).split(".")[0]

                fileext = file_name.group(0).split(".")[1]

                # convert file to bytes
                data = img_encoder(file_path, fileext)

                str_len = len(data)

                print(str_len)

                chunks = []

                chunks = break_into_chunks(data, 8000)

                await server.set(filename, len(chunks))
                await server.set(f"{filename}_ext", fileext)

                for i in range(len(chunks)):
                    print(f"Sending chunk {i}/{len(chunks)}")

                    await server.set(f"{filename}_{i}", chunks[i])

            else:  # Handle other types of files
                with open(file_path, 'rb') as file:
                    file_data = file.read()

        else:  # Handle regular input
            data = file_path.split(":")
            key = data[0]
            value = data[1]
            await server.set(key, value)

        print("\033c", end="")

    server.stop()


def break_into_chunks(original_bytes, chunk_size):
    chunks = []
    for i in range(0, len(original_bytes), chunk_size):
        chunk = original_bytes[i:i + chunk_size]
        chunks.append(chunk)
    return chunks


def img_encoder(filepath, fileext):
    # read img
    img = Image.open(filepath, 'r')
    buf = io.BytesIO()

    fileext = fileext.lower()

    if (fileext == "jpg" or fileext == "jpeg"):
        fileext = "JPEG"

    img.save(buf, format=fileext, quality=85, optimize=True, progressive=True)
    byte_im = buf.getvalue()

    return byte_im


if __name__ == "__main__":
    asyncio.run(run())
