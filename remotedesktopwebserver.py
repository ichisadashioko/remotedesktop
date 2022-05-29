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

import tqdm

import tornado
import tornado.gen
import tornado.ioloop
import tornado.web

import numpy as np
import PIL
import PIL.Image
import cv2

import mss
import pynput
import pynput.mouse

ROOT = os.path.dirname(os.path.abspath(__file__))
CURSOR_ICON_FILEPATH = os.path.join(ROOT, 'aero_arrow.png')
if not os.path.exists(CURSOR_ICON_FILEPATH):
    raise Exception(f'cursor icon file not found: {CURSOR_ICON_FILEPATH}')

CURSOR_BGRA_IMAGE = cv2.imread(CURSOR_ICON_FILEPATH, cv2.IMREAD_UNCHANGED)
CURSOR_HEIGHT, CURSOR_WIDTH = CURSOR_BGRA_IMAGE.shape[:2]
CACHED_NON_ALPHA_INDEX_LIST = []
for y in range(CURSOR_HEIGHT):
    x_index_list = []
    for x in range(CURSOR_WIDTH):
        bgra_pixel = CURSOR_BGRA_IMAGE[y, x]
        if bgra_pixel[3] != 0:
            x_index_list.append(x)
    CACHED_NON_ALPHA_INDEX_LIST.append(x_index_list)

MOUSE_CONTROLLER = pynput.mouse.Controller()


def merge_cursor(
    bgra_image: np.ndarray,
    location: tuple,
    monitor_region: dict,
):
    mousex, mousey = location
    monitor_left = monitor_region['left']
    monitor_top = monitor_region['top']
    monitor_right = monitor_region['left'] + monitor_region['width']
    monitor_bottom = monitor_region['top'] + monitor_region['height']

    if mousex < monitor_left or mousex > monitor_right:
        return

    if mousey < monitor_top or mousey > monitor_bottom:
        return

    image_height, image_width = bgra_image.shape[:2]
    for y in range(CURSOR_HEIGHT):
        real_y = y + mousey
        if real_y >= image_height:
            break

        color_index_list = CACHED_NON_ALPHA_INDEX_LIST[y]
        for x in color_index_list:
            real_x = x + mousex
            if real_x >= image_width:
                break

            bgra_image[real_y, real_x][0:3] = CURSOR_BGRA_IMAGE[y, x][0:3]


def capture_screen_to_image_bytes(
    screen_region: dict = None,
    encode_image_format_extension: str = '.png',
    scaling_factor: float = None,
    render_mouse_cursor: bool = False,
):
    with mss.mss() as sct:
        if screen_region is None:
            screen_region = sct.monitors[1]

        mss_image = sct.grab(screen_region)
        np_image = np.array(mss_image, dtype=np.uint8)

        if render_mouse_cursor:
            mouse_position = MOUSE_CONTROLLER.position
            merge_cursor(
                np_image,
                mouse_position,
                monitor_region=screen_region,
            )

        rgb_image = cv2.cvtColor(np_image, cv2.COLOR_BGRA2BGR)

        if scaling_factor is not None:
            rgb_image = cv2.resize(
                rgb_image,
                dsize=None,
                fx=scaling_factor,
                fy=scaling_factor,
                interpolation=cv2.INTER_NEAREST,
            )

        print(time.perf_counter_ns(), 'rgb_image.shape', rgb_image.shape, end='\r')
        status, bs = cv2.imencode(encode_image_format_extension, rgb_image)
        if status:
            return bs.tobytes()

        return None


def make_obj_json_friendly(obj):
    if isinstance(obj, (int, float, str)):
        return obj
    elif isinstance(obj, list):
        return [make_obj_json_friendly(x) for x in obj]
    elif isinstance(obj, dict):
        return {
            make_obj_json_friendly(k): make_obj_json_friendly(v) for k, v in obj.items()
        }
    else:
        return repr(obj)


def normalize_local_path_seperator(inpath):
    # windows can still work with forward slash
    return re.sub(r'[\\/]+', '/', inpath)


def is_child_path(parent_path, child_path):
    parent_path = normalize_local_path_seperator(parent_path)
    child_path = normalize_local_path_seperator(child_path)

    # windows hack
    parent_path = parent_path.lower()
    child_path = child_path.lower()

    print('parent_path', parent_path)
    print('child_path', child_path)

    return child_path.startswith(parent_path)


def render_static_directory_listing_html(
    normalized_request_path: str,
    child_filename_list: list,
):
    # black theme css
    html = f'''
<!DOCTYPE html>
<html>
<head>
<title>Directory listing for {normalized_request_path}</title>
<style>
* {{
    background-color: black !important;
    color: white !important;
}}
</style>
</head>
<body>
<h1>Directory listing for {normalized_request_path}</h1>
<ul>
'''
    # TODO render link for each path components
    for child_filename in child_filename_list:
        relative_url = f'./{child_filename}'
        html += f'''
<li><a href="{relative_url}">{child_filename}</a></li>
'''
    html += f'''
</ul>
</body>
</html>
'''
    return html


########################################################################
### STATIC FILE HANDLER FUNCTIONS ######################################
# static file handler


class InvalidCharacterInPath(Exception):
    pass


INVALID_CHARACTER_IN_PATH = ':*?\"<>|'


def normalize_request_path(request_path: str):
    # un-escaped characters
    unescaped_url = urllib.parse.unquote(request_path)
    # normalize path separators
    normalized_path_sep_url = re.sub(r'[\\/]+', '/', unescaped_url)

    path_components = normalized_path_sep_url.split('/')
    normalized_path_components = []
    for component in path_components:
        if component == '..':
            if len(normalized_path_components) > 0:
                normalized_path_components.pop()
        elif component in ('.', ''):
            pass
        else:
            normalized_path_components.append(component)

    normalized_path = '/'.join(normalized_path_components)
    # check for invalid characters
    for c in INVALID_CHARACTER_IN_PATH:
        if c in normalized_path:
            raise InvalidCharacterInPath(f'invalid character {c} in path')

    return normalized_path


########################################################################
RESPONSE_FILE_CHUNKS_SIZE = 8388608  # 8MB


def send_file_data(
    request_handler: tornado.web.RequestHandler,
    inpath: str,
    range_pair_list=None,
):
    with open(inpath, 'rb') as infile:
        if range_pair_list is not None:
            total_number_of_chunks = 0

            for range_pair in range_pair_list:
                remaining_bytes = range_pair[1] - range_pair[0]
                infile.seek(range_pair[0])

                number_of_chunks = int(math.ceil(remaining_bytes / RESPONSE_FILE_CHUNKS_SIZE))
                total_number_of_chunks += number_of_chunks

            pbar = tqdm.tqdm(total=total_number_of_chunks)
            for range_pair in range_pair_list:
                remaining_bytes = range_pair[1] - range_pair[0]
                infile.seek(range_pair[0])

                number_of_chunks = int(math.ceil(remaining_bytes / RESPONSE_FILE_CHUNKS_SIZE))
                for i in range(number_of_chunks):
                    read_data_size = int(min(RESPONSE_FILE_CHUNKS_SIZE, remaining_bytes))
                    data = infile.read(read_data_size)
                    request_handler.write(data)
                    remaining_bytes -= read_data_size

        else:
            # send whole file
            # the content size header and status code should have already been set before calling this function
            filesize = os.stat(inpath).st_size
            number_of_chunks = int(math.ceil(filesize / RESPONSE_FILE_CHUNKS_SIZE))
            pbar = tqdm.tqdm(range(number_of_chunks))
            remote_address = request_handler.request.connection.stream.socket.getpeername()
            description = f'{inpath} > {remote_address}'
            pbar.set_description(description)
            for _ in pbar:
                data = infile.read(RESPONSE_FILE_CHUNKS_SIZE)
                request_handler.write(data)


########################################################################
MIME_TYPE_DICT = {
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
}

TEXT_MIME_TYPE_LIST = [
    'text/html',
    'text/css',
    'text/javascript',
    'application/javascript',
    'application/json',
]


def get_mime_type_by_filename(
    filename: str,
):
    extension = os.path.splitext(filename)[1]
    extension = extension.lower()
    if extension in MIME_TYPE_DICT:
        return MIME_TYPE_DICT[extension]
    else:
        return 'application/octet-stream'


########################################################################
WEBDATA_DIRECTORY = os.path.join(ROOT, 'webdata')
VALID_HTML_INDEX_FILENAME_LIST = [
    'index.html',
    'index.htm',
]


def handle_webdata_request(
    request_handler: tornado.web.RequestHandler,
):
    request_path = request_handler.request.path
    # normalize request path
    try:
        normalized_request_path = normalize_request_path(request_path)
    except InvalidCharacterInPath as ex:
        print(ex)
        # unauthorize
        request_handler.set_status(403)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'invalid character in path',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    # join with webdata directory
    if len(normalized_request_path) == 0:
        local_path = WEBDATA_DIRECTORY
    elif normalized_request_path == '/':
        local_path = WEBDATA_DIRECTORY
    else:
        local_path = os.path.join(WEBDATA_DIRECTORY, normalized_request_path)

    if local_path == WEBDATA_DIRECTORY:
        pass
    elif not is_child_path(WEBDATA_DIRECTORY, local_path):
        # unauthorize
        request_handler.set_status(403)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'unauthorized access',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    # check if file exists
    if not os.path.exists(local_path):
        # not found
        request_handler.set_status(404)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'file not found',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    file_stat = os.stat(local_path)
    if stat.S_ISDIR(file_stat.st_mode):
        # automatically serve index.html
        # directory
        # check if index.html exists
        child_filename_list = os.listdir(local_path)
        for child_filename in child_filename_list:
            lowered_child_filename = child_filename.lower()
            if lowered_child_filename in VALID_HTML_INDEX_FILENAME_LIST:
                child_filepath = os.path.join(local_path, child_filename)
                # send modified time
                os.path.getmtime(child_filepath)
                # TODO
                request_handler.set_status(200)
                request_handler.set_header('Content-Type', 'text/html')
                filesize = os.stat(child_filepath).st_size
                if filesize > 0:
                    send_file_data(request_handler, child_filepath)
                return

        # not found
        # return directory listing
        # TODO option to disable directory listing
        # contruct static html page
        html_str = render_static_directory_listing_html(
            normalized_request_path,
            child_filename_list,
        )

        request_handler.set_status(200)
        request_handler.set_header('Content-Type', 'text/html')
        request_handler.write(html_str)
        return

    if not stat.S_ISREG(file_stat.st_mode):
        # unauthorize
        # this is not a regular file
        request_handler.set_status(403)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'this is not a regular file',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    # regular file
    # TODO parse and support Range header
    request_handler.set_status(200)
    mime_type = get_mime_type_by_filename(local_path)

    if mime_type in TEXT_MIME_TYPE_LIST:
        # set mime type and charset to utf-8
        header_value = f'{mime_type}; charset=utf-8'
        request_handler.set_header('Content-Type', header_value)
    else:
        request_handler.set_header('Content-Type', mime_type)

    filesize = os.stat(local_path).st_size
    request_handler.set_header('Content-Length', str(filesize))

    send_file_data(request_handler, local_path)


### END STATIC FILE HANDLER FUNCTIONS ##################################
########################################################################


class AllRequestHandler(tornado.web.RequestHandler):
    async def get(self):
        try:
            handle_webdata_request(
                request_handler=self,
            )

            return
        except Exception as ex:
            stack_trace_str = traceback.format_exc()
            print(ex)
            print(stack_trace_str)
            response_obj = {
                'message': ex,
                'exception': ex,
                'stack_trace': stack_trace_str,
                'request_handler': self,
            }

            response_obj = make_obj_json_friendly(response_obj)
            response_str = json.dumps(response_obj)
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.write(response_str)
            return

        # get the request path
        request_url = self.request.path
        self.set_header('Content-Type', 'application/json')
        self.write(repr({
            'request_url': request_url,
        }))

        return
        # DEBUG
        # set header to json
        self.set_header('Content-Type', 'application/json')
        self.write(repr(self.__dict__))
        # TODO

    async def post(self):
        try:
            request_path = self.request.path
            # TODO
            pass
        except Exception as ex:
            stack_trace_str = traceback.format_exc()
            print(ex)
            print(stack_trace_str)
            response_obj = {
                'message': ex,
                'exception': ex,
                'stack_trace': stack_trace_str,
                'request_handler': self,
            }

            response_obj = make_obj_json_friendly(response_obj)
            response_str = json.dumps(response_obj)
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.write(response_str)
            return

        self.set_header('Content-Type', 'application/json')
        json_friendly_obj = make_obj_json_friendly(self.__dict__)
        json_str = json.dumps(json_friendly_obj)
        self.write(json_str)
        # TODO


########################################################################
def web_parse_scaling_value(value_list: list):
    if len(value_list) == 0:
        return None

    value_bs = value_list[0]
    if len(value_bs) == 0:
        return None

    try:
        value_int = int(value_bs)
        if value_int < 1:
            return None

        return (1 / value_int)
    except Exception as ex:
        return None


def web_parse_image_format_value(value_list: list):
    if len(value_list) == 0:
        return None

    value_bs = value_list[0]
    if len(value_bs) == 0:
        return None

    try:
        value_str = value_bs.decode('ascii')
        value_str = value_str.lower()
        if value_str in ('png', 'jpg', 'jpeg'):
            return value_str
    except Exception as ex:
        pass

    return None


def web_parse_frame_rate_value(value_list: list):
    if len(value_list) == 0:
        return None

    value_bs = value_list[0]
    if len(value_bs) == 0:
        return None

    try:
        value_int = int(value_bs)
        if value_int < 1:
            return None

        return value_int
    except Exception as ex:
        return None


########################################################################
DEFAULT_FRAME_RATE = 32
MAX_FRAME_RATE = 128

DEFAULT_IMAGE_FORMAT = 'png'


class ImageStreamHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        params = self.request.query_arguments
        print(f'ImageStreamHandler: params: {params}')

        scaling_factor = None
        render_mouse_cursor = False
        image_format = DEFAULT_IMAGE_FORMAT
        frame_rate = DEFAULT_FRAME_RATE

        if 'scaling' in params:
            scaling_value_list = params['scaling']
            scaling_factor = web_parse_scaling_value(scaling_value_list)
        if 'cursor' in params:
            render_mouse_cursor = True
        if 'format' in params:
            image_format_value_list = params['format']
            retval = web_parse_image_format_value(image_format_value_list)
            if retval is not None:
                image_format = retval

        frame_rate_key_list = ['fps', 'framerate', 'frame_rate']
        for frame_rate_key in frame_rate_key_list:
            if frame_rate_key in params:
                frame_rate_value_list = params[frame_rate_key]
                retval = web_parse_frame_rate_value(frame_rate_value_list)
                if retval is not None:
                    frame_rate = retval
                    break

        if frame_rate > MAX_FRAME_RATE:
            frame_rate = DEFAULT_FRAME_RATE
        if frame_rate == 0:
            frame_rate = DEFAULT_FRAME_RATE

        sleep_time_seconds = 1.0 / frame_rate
        image_content_type_header = f'Content-Type: image/{image_format}\r\n'
        image_ext = f'.{image_format}'

        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--frame')

        while True:
            # check if connection is still alive
            if self.request.connection.stream.closed():
                print('connection closed')
                break

            self.write('--frame\r\n')
            self.write(image_content_type_header)

            bs = capture_screen_to_image_bytes(
                encode_image_format_extension=image_ext,
                scaling_factor=scaling_factor,
                render_mouse_cursor=render_mouse_cursor,
            )

            bs_len = len(bs)
            self.write(f'Content-Length: {bs_len}\r\n\r\n')
            self.write(bs)
            self.flush()
            time.sleep(sleep_time_seconds)
########################################################################


DEFAULT_SERVER_PORT = 21578


def main():
    parser = argparse.ArgumentParser(description='Remote desktop webserver')
    parser.add_argument('port', type=int, default=DEFAULT_SERVER_PORT, nargs='?')
    args = parser.parse_args()
    print('args', args)

    PORT_NUMBER = args.port

    app = tornado.web.Application([
        (r'/imagestream', ImageStreamHandler),
        (r'', AllRequestHandler),
        (r'/', AllRequestHandler),
        (r'/.*', AllRequestHandler),
    ])

    print(f'http://localhost:{PORT_NUMBER}')
    print(f'http://localhost:{PORT_NUMBER}/?cursor&fps=32&format=jpg')
    app.listen(PORT_NUMBER, address='0.0.0.0')
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
