import os
import io
import socket
import gzip
import time
import threading

import numpy as np
import PIL
import PIL.Image
import cv2

DEFAULT_SERVER_PORT = 21578

socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_connection.connect(('127.0.0.1', DEFAULT_SERVER_PORT))


CV2_WINDOW_NAME = 'frame'
cv2.namedWindow(CV2_WINDOW_NAME)

REFRESH_RATE = 60
WAIT_TIME_SECONDS = 1 / REFRESH_RATE
WAIT_TIME_MILLISECONDS = int(WAIT_TIME_SECONDS * 1000)

print('REFRESH_RATE', REFRESH_RATE)
print('WAIT_TIME_SECONDS', WAIT_TIME_SECONDS)

GLOBAL_STOP_FLAG = False
CURRENT_FRAME = None


def cv2_ui_thread_function():
    while not GLOBAL_STOP_FLAG:
        if os.path.exists('stop'):
            break

        if CURRENT_FRAME is not None:
            cv2.imshow(CV2_WINDOW_NAME, CURRENT_FRAME)
            cv2.waitKey(WAIT_TIME_MILLISECONDS)


cv2_ui_thread = threading.Thread(target=cv2_ui_thread_function)
cv2_ui_thread.start()


PENDING_DATA = b''
MODIFY_PENDING_DATA_LOCK = threading.Lock()


def process_data_thread_function():
    global PENDING_DATA
    global CURRENT_FRAME

    while not GLOBAL_STOP_FLAG:
        if os.path.exists('stop'):
            break

        if len(PENDING_DATA) < 4:
            try:
                time.sleep(WAIT_TIME_SECONDS)
            except Exception as ex:
                print(ex)
                continue

        image_data_size_bs = PENDING_DATA[:4]
        image_data_size = int.from_bytes(image_data_size_bs, byteorder='little')
        if len(PENDING_DATA) < (4 + image_data_size):
            try:
                time.sleep(WAIT_TIME_SECONDS)
            except Exception as ex:
                print(ex)
                continue

        image_data_bs = PENDING_DATA[4:4 + image_data_size]
        with MODIFY_PENDING_DATA_LOCK:
            PENDING_DATA = PENDING_DATA[4 + image_data_size:]

        np_buffer = np.frombuffer(image_data_bs, dtype=np.uint8)
        frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
        CURRENT_FRAME = frame


process_data_thread = threading.Thread(target=process_data_thread_function)
process_data_thread.start()

while True:
    if os.path.exists('stop'):
        break

    bs = socket_connection.recv(65536)
    bs_len = len(bs)
    print(time.perf_counter_ns(), bs_len)
    if bs_len == 0:
        break

    with MODIFY_PENDING_DATA_LOCK:
        PENDING_DATA += bs
