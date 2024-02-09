import asyncio
from kademlia.network import Server
import aioconsole
import sys
from PIL import Image
import os
import re
import io
import logging
import csv
import time
from lorem_text import lorem

# disable logging
logging.getLogger('kademlia').setLevel(logging.CRITICAL)


IMG_WRITE_HEADER = ['File_Name', 'File_Size',
                    'Number_Chunks', 'Average_Chunk_Size', 'Number_Bytes', 'Write_Duration']
IMG_READ_HEADER = ['File_Name', 'File_Size', 'Number_Chunks', 'Read_Duration']

STR_WRITE_HEADER = ['Key', 'Value_Length', 'Write_Duration']
STR_READE_HEADER = ['Key', 'Value_Length', 'Read_Duration']

DEFINED_IMG = ['1_24kb.jpeg', 
               '2_360kb.png', 
               '3_2mb.jpg', 
               '4_10mb.png', 
               '5_15mb.png', 
               '6_18mb.png', 
               '7_19mb.png']

DEFINED_IMG_NO_EXTENSION = ['1_24kb',
                            '2_360kb',
                            '3_2mb',
                            '4_10mb',
                            '5_15mb',
                            '6_18mb',
                            '7_19mb']

def init_csv(filename, header):
    if not os.path.exists("report"):
        os.makedirs("report")
    if not os.path.isfile(filename):
        with open(filename, 'a+') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            file.close()


def write_csv(filename, data):
    with open(filename, 'a') as file:
        writer = csv.writer(file)
        writer.writerow(data)
        file.close()


async def start_node(port=int(sys.argv[1]), bootstrap_node=int(sys.argv[2])):
    server = Server()
    await server.listen(port)
    if bootstrap_node:
        bootstrap_address = ("127.0.0.1", bootstrap_node)
        await server.bootstrap([bootstrap_address])
    return server


async def set(node, key, value):
    await node.set(key, value)


async def get(node, key):
    return await node.get(key)


async def run_interactive_loop(node):
    while True:
        action = (await aioconsole.ainput("Set [s], Get [g], or Quit [q]: "))
        if action == "q":
            print("Quit")
            break
        elif action == "s":
            t = (await aioconsole.ainput("Enter type <key,value> [kv], image [img], defined img [ai] lorem mode[l]: "))
            if t == "img":
                filepath = (await aioconsole.ainput("Enter the file path [.jpg|.jpeg|.png]: "))
                await set_img(node, filepath.strip())
            elif t == "ai":
                for img in DEFINED_IMG:
                    await set_img(node, f"to_send/{img}")
            elif t == "l":
                for i in range(0, 1005, 5):
                    key = f"lorem_{i}"
                    value = lorem.words(i)
                    await set_str(node, key, value)
            elif t == "kv":
                key = (await aioconsole.ainput("Enter the key: "))
                value = (await aioconsole.ainput("Enter the value: "))
                await set_str(node, key, value)
            else:
                print("Invalid input.")
        elif action == "g":
            t = (await aioconsole.ainput("Enter type key [k], image [img], defined img [ai], lorem mode [l]: "))
            if t == "k":
                key = (await aioconsole.ainput("Enter the key: "))
                print(await get_str(node, key.strip()))
            elif t == "ai":
                for name in DEFINED_IMG_NO_EXTENSION:
                    await get_img(node, name)
            elif t == "l":
                for i in range(0, 1005, 5):
                    key = f"lorem_{i}"
                    await get_str(node, key)
            elif t == "img":
                key = (await aioconsole.ainput("Enter img name: "))
                await get_img(node, key.strip())
            else:
                print("Invalid input.")
        else:
            print("Invalid input.")


async def set_str(node, key, value):
    start_time = time.time()
    await set(node, key, value)
    write_duration = time.time() - start_time

    # report
    write_csv('./report/str_write.csv', [key, len(value), write_duration])


async def get_str(node, key):
    start_time = time.time()
    value = await get(node, key)
    read_duration = time.time() - start_time

    # report
    write_csv('./report/str_read.csv', [key, len(value), read_duration])
    return value


async def get_img(node, key):
    chunks = []

    start_time = time.time()

    chunks_len = await get(node, key)

    if not chunks_len:
        print(f"File {key} not found")
        return

    for i in range(int(chunks_len)):
        chunks.append(await get(node, f"{key}_{i}"))

    read_duration = time.time() - start_time

    data = join_byte_chunks(chunks)
    file_saver(data, key)

    # report
    write_csv('./report/img_read.csv',
              [key,
               os.path.getsize(f"download/{key}.JPEG"),
               len(chunks),
               read_duration])


async def set_img(node, filepath):
    if filepath.startswith("'") and filepath.endswith("'") \
            or filepath.startswith('"') and filepath.endswith('"'):
        filepath = filepath[1:-1]

    if os.path.isfile(filepath):
        if filepath.lower().endswith(('.jpg', '.jpeg', '.png')):

            filename = re.search(
                r"([a-zA-Z0-9\s_\\.\-\(\):])+(.jpg|.jpeg|.png)$", filepath)

            file_name = filename.group(0).split(".")[0]

            # convert file to bytes
            data = img_encoder(filepath)

            chunks = []
            chunks = break_into_chunks(data, 8000)

            start_time = time.time()

            await set(node, file_name, len(chunks))

            for i in range(len(chunks)):
                print(f"Uploading chunk {i+1}/{len(chunks)}")
                print("\033c", end="")
                await set(node, f"{file_name}_{i}", chunks[i])

            # report
            write_duration = time.time() - start_time

            average_chunk_size = len(data) / len(chunks)

            # report

            write_csv('./report/img_write.csv',
                      [file_name,
                       os.path.getsize(filepath),
                       len(chunks),
                       (average_chunk_size),
                       len(data),
                       write_duration])

        else:
            pass


def break_into_chunks(original_bytes, chunk_size):
    chunks = []
    for i in range(0, len(original_bytes), chunk_size):
        chunk = original_bytes[i:i + chunk_size]
        chunks.append(chunk)
    return chunks


def img_encoder(filepath):
    # read img
    img = Image.open(filepath, 'r')
    buf = io.BytesIO()

    img = img.convert('RGB')
    img.save(buf, format="JPEG", quality=85, optimize=True, progressive=True)
    byte_im = buf.getvalue()

    return byte_im


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


def file_saver(data, filename):
    '''
    Create folder name download in Client directory if not exists
    Save file to download folder

    @param data: bytes - image in bytes
    @param filename: str - name of file without extension
    '''
    if not os.path.exists("download"):
        os.makedirs("download")
    img_decoder(data).save(f"download/{filename}.JPEG")
    print(f"File saved as {filename}.JPEG")
    return


async def main():

    node = None
    try:
        node = await start_node()
        await run_interactive_loop(node)
    finally:
        if node:
            node.stop()

if __name__ == "__main__":

    init_csv('./report/img_write.csv', IMG_WRITE_HEADER)
    init_csv('./report/img_read.csv', IMG_READ_HEADER)
    init_csv('./report/str_write.csv', STR_WRITE_HEADER)
    init_csv('./report/str_read.csv', STR_READE_HEADER)

    asyncio.run(main())
