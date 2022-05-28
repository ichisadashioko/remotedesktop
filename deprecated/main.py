import os
import io
import socket
import gzip
import time

import numpy as np
import PIL
import PIL.Image
import cv2

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

FRAME_RATE = 12
WAIT_TIME_SECONDS = 1 / FRAME_RATE
WAIT_TIME_NS = WAIT_TIME_SECONDS * 10 ** 9
LAST_FRAME_TIME_NS = 0
CURRENT_FRAME_TIME_NS = 0

print('FRAME_RATE', FRAME_RATE)
print('WAIT_TIME_SECONDS', WAIT_TIME_SECONDS)
print('WAIT_TIME_NS', WAIT_TIME_NS)

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
    # CLIENT_SOCKET.send(width_bs)
    # CLIENT_SOCKET.send(height_bs)

    # TODO while True
    while True:
        if os.path.exists('stop'):
            break

        CURRENT_FRAME_TIME_NS = time.perf_counter_ns()
        DELTA_TIME_NS = CURRENT_FRAME_TIME_NS - LAST_FRAME_TIME_NS
        # print(f'DELTA_TIME_NS: {DELTA_TIME_NS}')
        if DELTA_TIME_NS < WAIT_TIME_NS:
            DELTA_TIME_SECONDS = DELTA_TIME_NS / 10 ** 9
            # print(f'DELTA_TIME_SECONDS: {DELTA_TIME_SECONDS}')
            time.sleep(DELTA_TIME_SECONDS)

        mss_image = sct.grab(default_monitor)
        LAST_FRAME_TIME_NS = time.perf_counter_ns()
        # print('LAST_FRAME_TIME_NS', LAST_FRAME_TIME_NS)

        # print('type(mss_image)', type(mss_image))

        # compress the data
        # raw_image_data = mss_image.raw
        # remove the alpha channel
        # raw_image_data_without_alpha = raw_image_data[:, :, :3]
        # raw_rgb_image_data = mss_image.rgb
        np_image = np.array(mss_image, dtype=np.uint8)
        rgb_image = cv2.cvtColor(np_image, cv2.COLOR_BGRA2BGR)

        # status, png_bytes = cv2.imencode('.png', rgb_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        # png_bytes_len = len(png_bytes)
        # print(time.perf_counter_ns(), 'png_bytes_len <= 0')
        # if png_bytes_len <= 0:
        #     continue
        status, bs = cv2.imencode('.jpg', rgb_image)
        bs_len = len(bs)
        print(time.perf_counter_ns(), 'len(bs)', bs_len, end='\r')

        if bs_len <= 0:
            continue

        data_size_bs = bs_len.to_bytes(4, byteorder='little')
        CLIENT_SOCKET.send(data_size_bs)
        CLIENT_SOCKET.send(bs)
