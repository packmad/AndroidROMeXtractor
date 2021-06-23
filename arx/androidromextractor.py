import logging
import os
import tempfile

from pathlib import Path
from typing import Dict, Set, Callable, Optional, List
from os.path import isdir, isfile, basename, join

from arx.sdat2img.sdat2img import sdat2img
from arx.shell_wrapper import aunpack, findw, find, mount, catfiles, resize2fs, unyaffs
from arx.utility import find_biggest_archive, filetype_to_files
from arx.formats_extraction import \
    extract_pac, \
    extract_kdz, \
    extract_dz, \
    extract_sin, \
    extract_ota_payload_bin, \
    extract_br, \
    extract_ubi_image, \
    sparsechunks_to_raw, \
    sparse_single_to_raw, \
    extract_update_app, \
    extract_sign_img, \
    extract_lz4, \
    unsparse_joiner

logger = logging.getLogger('rom_analyzer')


def unpack_archive(in_file: str, unpack_dir: str) -> bool:
    assert isfile(in_file)
    assert isdir(unpack_dir)
    if aunpack(in_file, unpack_dir):
        biggest_archive = find_biggest_archive(unpack_dir)
        if biggest_archive is not None and biggest_archive != in_file:
            return aunpack(biggest_archive, unpack_dir)
        return True
    return False


def add_mount(diz: dict, tmp_dir: str, img_path: str):
    assert isdir(tmp_dir)
    assert isfile(img_path)
    bname = os.path.basename(img_path)
    assert bname not in diz
    mnt_point = tempfile.mkdtemp(dir=tmp_dir)
    if mount(img_path, mnt_point):
        diz[bname] = mnt_point
        logger.info("{} -> {}".format(bname, diz))
    else:
        logger.error("Mount failed! Img={}".format(bname))
        if 'system' in bname.lower():
            raise Exception('Mount of system failed!')


def search_and_unpack(work_dir: str, patt_wild: str, unpack_method: Callable):
    imgs = findw(work_dir, patt_wild)
    if imgs is not None:
        for img in imgs:
            if not unpack_method(img):
                raise Exception(f"'{patt_wild}' search and unpack failed")


def unpack_and_mount(in_file: str, work_dir: str = None, mnt_dir: str = None) -> Dict:
    assert isfile(in_file)
    if work_dir is None:
        work_dir = tempfile.mkdtemp()
    assert isdir(work_dir)
    if mnt_dir is not None:
        assert os.path.isdir(mnt_dir)

    if not unpack_archive(in_file, work_dir):
        raise Exception("Unpack failed")

    update_app = find(work_dir, "UPDATE.APP")
    if update_app is not None and not extract_update_app(update_app):
        raise Exception("extract_update_app failed")

    payload_ota = find(work_dir, "payload.bin")
    if payload_ota is not None and not extract_ota_payload_bin(payload_ota, work_dir):
        raise Exception("extract_ota_payload_bin failed")

    rawprogram0_xml = find(work_dir, 'rawprogram0.xml')
    if rawprogram0_xml is not None and not unsparse_joiner(rawprogram0_xml):
        raise Exception("unsparse_joiner failed")

    search_and_unpack(work_dir, "*pac", extract_pac)
    search_and_unpack(work_dir, "*-sign.img", extract_sign_img)
    search_and_unpack(work_dir, "*.lz4", extract_lz4)
    search_and_unpack(work_dir, "*.br", extract_br)
    search_and_unpack(work_dir, "*.sin", extract_sin)
    search_and_unpack(work_dir, "*.kdz", extract_kdz)
    search_and_unpack(work_dir, "*.dz", extract_dz)

    trlist: Optional[List[str]] = findw(work_dir, "*.transfer.list")
    if trlist is not None:
        for tr in trlist:
            new_dat = tr.replace('.transfer.list', '.new.dat')
            assert isfile(new_dat)
            new_img = os.path.join(work_dir, f"{basename(new_dat)}.img")
            sdat2img(tr, new_dat, new_img)
            assert isfile(new_img)
            os.remove(new_dat)

    diz_filetype_to_files = filetype_to_files(work_dir)
    logger.debug(diz_filetype_to_files)
    ret_diz = {}
    for file_type, list_files in diz_filetype_to_files.items():
        file_type: str
        if 'ext4 filesystem data' in file_type or 'ext2 filesystem data' in file_type:
            for f in list_files:
                if f.endswith('_1.img') and rawprogram0_xml is None:
                    name = basename(f).replace('_1.img', '')
                    parent_folder = Path(f).parent
                    splits = [f]
                    i = 1
                    while True:
                        i += 1
                        succ_split = join(parent_folder, f'{name}_{i}.img')
                        if isfile(succ_split):
                            splits.append(succ_split)
                        else:
                            break
                    out_file = join(parent_folder, f'{name}.img')
                    assert not isfile(out_file)
                    if not catfiles(splits, out_file):
                        raise Exception('catfiles failed')
                    f = out_file
                elif 'needs journal recovery' in file_type:
                    assert resize2fs(f)
                add_mount(ret_diz, work_dir, f)
        if file_type.startswith('Android sparse image'):
            sparsechunk_names: Set[str] = set()
            for f in list_files:
                if 'sparsechunk' in f:
                    bname = os.path.basename(f)
                    sparsechunk_names.add(bname.split('.')[0])
                    continue
                raw = sparse_single_to_raw(f)
                add_mount(ret_diz, work_dir, raw)
            if len(sparsechunk_names) > 0:
                logger.info("Sparsechunks found: {}".format(sparsechunk_names))
            for sc_name in sparsechunk_names:
                raw = sparsechunks_to_raw(work_dir, sc_name)
                add_mount(ret_diz, work_dir, raw)
        if file_type.startswith('UBI image'):
            raise Exception("UBI unsupported")  #TODO
            #for f in list_files:
                #if not extract_ubi_image(f):

                #add_mount(ret_diz, work_dir, f)
        if file_type == 'YAFFS':
            for f in list_files:
                bname = os.path.basename(f)
                assert bname not in ret_diz
                mnt_point = tempfile.mkdtemp(dir=work_dir)
                unyaffs(f, mnt_point)
                ret_diz[bname] = mnt_point
                logger.info("{} -> {}".format(bname, ret_diz))
    boot_img = find(work_dir, 'boot.img')
    if boot_img is not None:
        ret_diz['boot'] = boot_img
    ramdisk_img = find(work_dir, 'ramdisk.img')
    if ramdisk_img is not None:
        ret_diz['ramdisk'] = ramdisk_img
    return ret_diz
