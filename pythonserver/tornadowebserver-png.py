import os
import pickle
import posixpath
import argparse
import time
import io
import threading
import json
import re
import stat
import math
import traceback

import urllib
import urllib.parse

import tornado
import tornado.gen
import tornado.ioloop
import tornado.web

import numpy as np
import PIL
import PIL.Image
import cv2

import mss


with mss.mss() as sct:
    default_monitor = sct.monitors[1]
    print('default_monitor', default_monitor)


def current_screen_in_png_string(reduce_size_by_factor: int = None):
    with mss.mss() as sct:
        mss_image = sct.grab(default_monitor)
        np_image = np.array(mss_image, dtype=np.uint8)
        rgb_image = cv2.cvtColor(np_image, cv2.COLOR_BGRA2BGR)

        tmp = None

        if reduce_size_by_factor is not None:
            tmp = 1/reduce_size_by_factor
            rgb_image = cv2.resize(
                rgb_image,
                dsize=None,
                fx=tmp,
                fy=tmp,
                interpolation=cv2.INTER_NEAREST,
            )

        print(time.perf_counter_ns(), 'rgb_image.shape', rgb_image.shape, 'tmp', tmp, end='\r')

        status, bs = cv2.imencode('.png', rgb_image)
        return bs.tobytes()


FRAME_RATE = 30
WAIT_TIME_SECONDS = 1 / FRAME_RATE
WAIT_TIME_NS = WAIT_TIME_SECONDS * 10 ** 9
LAST_FRAME_TIME_NS = 0
CURRENT_FRAME_TIME_NS = 0


class MainHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, reduce_size_by_factor=None):
        if type(reduce_size_by_factor) is str:
            reduce_size_by_factor = int(reduce_size_by_factor)

        print('reduce_size_by_factor', reduce_size_by_factor)

        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--frame')
        while True:
            # check if connection is still alive
            if self.request.connection.stream.closed():
                print('connection closed')
                break

            self.write('--frame\r\n')
            self.write('Content-Type: image/png\r\n')

            bs = current_screen_in_png_string(reduce_size_by_factor)
            bs_len = len(bs)
            self.write(f'Content-Length: {bs_len}\r\n\r\n')
            self.write(bs)
            self.flush()
            time.sleep(WAIT_TIME_SECONDS)


app = tornado.web.Application([
    (r'/', MainHandler),
    (r'/([0-9]+)', MainHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static'}),
])


SERVER_PORT = 21578
print(f'http://localhost:{SERVER_PORT}')
app.listen(SERVER_PORT, address='0.0.0.0')
tornado.ioloop.IOLoop.current().start()
