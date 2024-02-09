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

# for csv headers
IMG_WRITE_HEADER = ['File_Name', 'File_Size',
                    'Number_Chunks', 'Average_Chunk_Size', 'Number_Bytes', 'Write_Duration']
IMG_READ_HEADER = ['File_Name', 'File_Size', 'Number_Chunks', 'Read_Duration']

STR_WRITE_HEADER = ['Key', 'Value_Length', 'Write_Duration']
STR_READE_HEADER = ['Key', 'Value_Length', 'Read_Duration']


# for testing image upload and download

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

node = None


def init_csv(filename, header):
    if not os.path.exists("report"):
        os.makedirs("report")

    # remove file if exists
    if os.path.isfile(filename):
        os.remove(filename)

    if not os.path.isfile(filename):
        with open(filename, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            file.close()


def write_csv(filename, data):
    with open(filename, 'a') as file:
        writer = csv.writer(file)
        writer.writerow(data)
        file.close()

# connect to the network and listen to the port


async def init_node(port=int(sys.argv[2]), existing_node=int(sys.argv[1])):
    server = Server()
    await server.listen(port)
    if existing_node:
        bootstrap_node = ("127.0.0.1", existing_node)
        await server.bootstrap([bootstrap_node])
    return server

# DHT set


async def set(node, key, value):
    await node.set(key, value)

# DHT get


async def get(node, key):
    return await node.get(key)

# DHT run


async def run(node):
    while True:
        action = (await aioconsole.ainput("Set [s], Get [g], Clear Screen[c] or Quit [q]: "))
        action = action.lower().strip()
        if action == "q":
            print("Quit")
            break
        elif action == "c":
            print("\033c", end="", flush=True)
        elif action == "s":
            t = (await aioconsole.ainput("Enter type <key,value> [kv], image [img], defined img [ai] lorem mode[l]: "))
            t = t.lower().strip()
            if t == "img":
                filepath = (await aioconsole.ainput("Enter the file path [.jpg|.jpeg|.png]: "))
                await set_img(node, filepath.strip())
            elif t == "ai":
                for img in DEFINED_IMG:
                    await set_img(node, f"to_send/{img}")
            elif t == "l":
                '''
                Lorem ipsum mode to test the DHT
                Set 200 key, value pairs with key as lorem_{i} and value as lorem ipsum text
                '''
                for i in range(0, 1005, 5):
                    key = f"lorem_{i}"
                    value = lorem.words(i)
                    await set_str(node, key, value)
                print("Set 1000 lorem ipsum key, value pairs.")
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
                print("Get 1000 lorem ipsum key, value pairs.")
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
    '''
    Get image from DHT
    1. Get the number of chunks
    2. Get all the chunks
    3. Join the chunks to form the original image
    4. Save the image to download folder
    '''
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
    '''
    Set image to DHT
    Each key is limited to len() <= 8000
    For any image, lower quality to 85% of original quality
    Then, it will be broken into chunks of 8000 bytes

    ONLY take in .jpg, .jpeg, .png files, test limit to 20mb file

    1. Set IMAGE_NAME:NUMBER_OF_CHUNKS
    2. SET all the chunks with the key IMAGE_NAME_i where i is the index of the chunk
    '''
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
            chunks = break_into_chunks(data)

            start_time = time.time()

            await set(node, file_name, len(chunks))

            for i in range(len(chunks)):
                await set(node, f"{file_name}_{i}", chunks[i])

            print(f"File {file_name} uploaded")

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


def break_into_chunks(original_bytes, chunk_size=8000):
    chunks = []
    for i in range(0, len(original_bytes), chunk_size):
        chunk = original_bytes[i:i + chunk_size]
        chunks.append(chunk)
    return chunks


def img_encoder(filepath):
    '''
    lower quality to 85% of original quality
    use JPEG format to reduce file size
    '''
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
    '''
    Join byte chunks to form a single byte string, result in original image
    '''
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

    try:
        node = await init_node()
        await run(node)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if node:
            print("Stopping this node...")
            node.stop()

if __name__ == "__main__":

    # clear the screen at run
    print("\033c", end="", flush=True)

    # create csv files for report
    init_csv('./report/img_write.csv', IMG_WRITE_HEADER)
    init_csv('./report/img_read.csv', IMG_READ_HEADER)
    init_csv('./report/str_write.csv', STR_WRITE_HEADER)
    init_csv('./report/str_read.csv', STR_READE_HEADER)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if node:
            print("Stopping this node...")
            node.stop()
