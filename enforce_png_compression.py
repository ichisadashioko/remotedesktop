#!/usr/bin/env python3
# encoding=utf-8
import os
import io
import sys
import subprocess
import argparse
from typing import List
import stat
import shutil

import numpy as np
import cv2


ROOT = os.path.dirname(os.path.abspath(__file__))
BAK_DIR = os.path.join(ROOT, 'bak')


class TermColor:
    RESET_COLOR = '\033[0m'
    FG_RED = '\033[31m'
    FG_GREEN = '\033[32m'
    FG_YELLOW = '\033[33m'
    FG_BLUE = '\033[34m'
    FG_BRIGHT_RED = '\033[91m'
    FG_BRIGHT_GREEN = '\033[92m'
    FG_BRIGHT_YELLOW = '\033[93m'
    FG_BRIGHT_BLUE = '\033[94m'
    FG_BRIGHT_MAGENTA = '\033[95m'


class Encoding:
    UTF8 = 'utf-8'
    UTF8_WITH_BOM = 'utf-8-sig'
    UTF16 = 'utf-16'
    GB2312 = 'gb2312'
    SHIFT_JIS = 'shift-jis'

    @classmethod
    def decode(cls, bs: bytes):
        try:
            encoding = cls.UTF8_WITH_BOM
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.UTF8
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.UTF16
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.GB2312
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.SHIFT_JIS
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        return None, bs


IGNORED_FILENAME_LIST = [
    '.git',  # git directory
    'logs',  # log directory
    'backup',  # Visual Studio project migration files
    # known Visual Studio files
    'bin',
    'obj',
    '.vs',
    'debug',
    'release',
    '.ipynb_checkpoints',
    '__pycache__',
    'bak',
]


def find_all_png_files(infile: str) -> List[str]:
    basename = os.path.basename(infile)
    if basename.lower() in IGNORED_FILENAME_LIST:
        return []

    retval = []

    file_stat = os.stat(infile)

    if stat.S_ISDIR(file_stat.st_mode):
        child_filename_list = os.listdir(infile)
        for fname in child_filename_list:
            fpath = os.path.join(infile, fname)
            retval.extend(find_all_png_files(fpath))
    elif stat.S_ISREG(file_stat.st_mode):
        ext = os.path.splitext(infile)[1].lower()
        ext = ext.lower()
        if ext == '.png':
            retval.append(infile)

    return retval


def get_png_files_from_tracked_git_files(indir: str):
    git_process = subprocess.run(
        args=['git', 'ls-files'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=indir,
    )

    if len(git_process.stderr) > 0:
        _, error_msg = Encoding.decode(git_process.stderr)

        if type(error_msg) is bytes:
            error_msg = str(error_msg)

        raise Exception(error_msg)

    encoding, decoded_output = Encoding.decode(git_process.stdout)
    if (encoding is None) or (type(decoded_output) is bytes):
        print(git_process.stdout)
        raise Exception('Failed to decode the git output!')

    output_lines = decoded_output.split('\n')
    relative_filepath_list = filter(lambda x: len(x) > 0, output_lines)
    filepath_list = map(lambda x: os.path.join(indir, x), relative_filepath_list)
    existing_filepath_list = filter(lambda x: os.path.exists(x), filepath_list)

    # If the file appears in git but it is a directory then it is probably a git submodule
    # TODO modules which are not initialized may appear as files
    regular_file_filepath_list = filter(lambda x: os.path.isfile(x), existing_filepath_list)
    png_filepath_list = filter(lambda x: os.path.splitext(x)[1].lower() == '.png', regular_file_filepath_list)
    png_filepath_list = list(png_filepath_list)
    return png_filepath_list


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('infile', default='.', action='store', nargs='?')
    parser.add_argument('--git', help='use git to list file', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()
    print(args)

    png_filepath_list = []

    infile = args.infile
    if not os.path.exists(infile):
        raise Exception(f'{infile} does not exist!')

    file_stat = os.stat(infile)

    if stat.S_ISREG(file_stat.st_mode):
        ext = os.path.splitext(infile)[1]
        ext = ext.lower()
        if ext == '.png':
            png_filepath_list.append(infile)
    elif stat.S_ISDIR(file_stat.st_mode):
        file_list = os.listdir(args.infile)

        for file_name in file_list:
            if file_name == '.git':
                args.git = True
                break

        if args.git:
            png_filepath_list = get_png_files_from_tracked_git_files(args.infile)
        else:
            png_filepath_list = find_all_png_files(args.infile)

    MAX_FILESIZE = 1024 * 1024 * 10  # 10 MBs
    for filepath in png_filepath_list:
        print('>', filepath, end=' ')

        filename = os.path.basename(filepath)

        filesize = os.path.getsize(filepath)
        if (filesize == 0) or (filesize > MAX_FILESIZE):
            print('\r', end='')
            continue

        original_bs = open(filepath, 'rb').read()
        np_buffer = np.frombuffer(original_bs, dtype=np.uint8)
        cv2_img = cv2.imdecode(np_buffer, cv2.IMREAD_UNCHANGED)

        if cv2_img is None:
            print(f' - {TermColor.FG_RED}cannot read image{TermColor.END}')
            continue

        status, np_buffer = cv2.imencode('.png', cv2_img, params=[cv2.IMWRITE_PNG_COMPRESSION, 9])
        if not status:
            print(f' - {TermColor.FG_RED}cannot encode image{TermColor.END}')
            continue

        enforced_image_bs = np_buffer.tobytes()
        if enforced_image_bs == original_bs:
            if args.verbose:
                print(f'{TermColor.FG_BRIGHT_GREEN}OK{TermColor.RESET_COLOR}')
            else:
                print('\r', end='')
        else:
            if args.run:
                file_stat = os.stat(filepath)
                modified_time_ns = file_stat.st_mtime_ns
                backup_fpath = os.path.join(BAK_DIR, f'{modified_time_ns}-{filename}')
                print(f' -> {TermColor.FG_BRIGHT_YELLOW}{backup_fpath}{TermColor.RESET_COLOR}', end=' ')

                ########################################################
                parent_dir, _ = os.path.split(backup_fpath)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)

                shutil.move(filepath, backup_fpath)
                open(filepath, mode='wb').write(enforced_image_bs)
                ########################################################

                print(f'{TermColor.FG_RED}x{TermColor.RESET_COLOR} -> {TermColor.FG_BRIGHT_GREEN}OK{TermColor.RESET_COLOR}')
            else:
                print(f'{TermColor.FG_RED}x{TermColor.RESET_COLOR}')


if __name__ == '__main__':
    main()
