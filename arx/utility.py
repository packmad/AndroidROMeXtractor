import os
import magic

from collections import defaultdict
from os.path import isdir, isfile
from typing import Optional, Dict, List
from pathlib import Path


from arx.shell_wrapper import findw


def get_parent_folder(file_path: str) -> str:
    return str(Path(file_path).parent)


def get_biggest_file(files_list: list) -> str:
    assert files_list is not None
    assert len(files_list) > 0

    max_file = files_list[0]
    max_size = os.path.getsize(max_file)
    for f in files_list:
        sz = os.path.getsize(f)
        if sz > max_size:
            max_file = f
            max_size = sz
    return max_file


def find_biggest_archive(directory: str) -> Optional[str]:
    assert os.path.isdir(directory)
    archives = ["rar", "zip", "7z", "ftf", "md5"]
    for a in archives:
        fw = findw(directory, '*' + a)
        if fw is not None:
            return get_biggest_file(fw)
    return None


def is_YAFFS(binary):
    return open(binary, "rb").read(12).upper() == b"\x03\x00\x00\x00\x01\x00\x00\x00\xFF\xFF\x00\x00".upper()


def filetype_to_files(folder: str, filter_size_bytes: int = 10**7) -> Dict[str, List[str]]:
    assert os.path.isdir(folder)
    diz = defaultdict(list)
    for root, dirs, files in os.walk(folder, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            if os.path.getsize(file) > filter_size_bytes:
                magic_type = magic.from_file(file)
                if magic_type.startswith('Android sparse image'):
                    magic_type = "".join(magic_type.split(',')[0:2])
                if magic_type == 'data' and is_YAFFS(file):
                    magic_type = 'YAFFS'
                diz[magic_type].append(file)
    return diz
