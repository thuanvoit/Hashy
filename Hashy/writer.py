import csv
import os

IMG_WRITE_HEADER = ['File_Name', 'File_Size',
                    'Number_Chunks','Average_Chunk_Size', 'Number_Bytes', 'Write_Duration']
IMG_READ_HEADER = ['File_Name', 'File_Size', 'Number_Chunks', 'Read_Duration']

STR_WRITE_HEADER = ['Key', 'Value_Length', 'Write_Duration']
STR_READE_HEADER = ['Key', 'Value_Length', 'Read_Duration']


def init_csv(filename, header):
    if not os.path.exists("report"):
        os.makedirs("report")
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(header)

def write_csv(filename, data):
    with open(filename, 'a') as file:
        writer = csv.writer(file)
        writer.writerow(data)
