import os
import io
import socket
import gzip

import numpy as np

import mss

SERVER_PORT = 21578
GLOBAL_FRAME_BUFFER = []

SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_SOCKET.bind(('0.0.0.0', SERVER_PORT))

# TODO print all network interfaces name and readable ip

print(f'waiting for connection on port {SERVER_PORT}')
SERVER_SOCKET.listen(1)
print('receiveing connection')
CLIENT_SOCKET, CLIENT_ADDRESS = SERVER_SOCKET.accept()
print('accepted connection')
print(f'connected to {CLIENT_ADDRESS}')

with mss.mss() as sct:
    # print(type(sct.monitors))
    # print(len(sct.monitors))
    # for i in range(len(sct.monitors)):
    #     print(f'{i} - {sct.monitors[i]}')

    default_monitor = sct.monitors[1]
    print('default_monitor', default_monitor)
    # TODO send width and height information
    width = default_monitor['width']
    height = default_monitor['height']
    print(f'width: {width} height: {height}')
    width_bs = width.to_bytes(4, byteorder='little')
    height_bs = height.to_bytes(4, byteorder='little')
    print('width_bs', width_bs)
    print('height_bs', height_bs)
    CLIENT_SOCKET.send(width_bs)
    CLIENT_SOCKET.send(height_bs)

    # TODO while True
    while True:
        if os.path.exists('stop'):
            break

        mss_image = sct.grab(default_monitor)
        # print('type(mss_image)', type(mss_image))

        # compress the data
        # raw_image_data = mss_image.raw
        # remove the alpha channel
        # raw_image_data_without_alpha = raw_image_data[:, :, :3]
        raw_rgb_image_data = mss_image.rgb
        # TODO run the compression call in a separate thread
        gzip_compressed_data_bs = gzip.compress(raw_rgb_image_data, compresslevel=9)

        # send the data
        size_of_data = len(gzip_compressed_data_bs)
        print(f'sending {size_of_data} bytes')
        # check if the data is too big to send
        if size_of_data > 1024 * 1024 * 10:
            print('data too big to send')
            continue

        data_size_bs = size_of_data.to_bytes(4, byteorder='little')
        CLIENT_SOCKET.send(data_size_bs)
        CLIENT_SOCKET.send(gzip_compressed_data_bs)
