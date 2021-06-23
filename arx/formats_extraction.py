import os
import xml.etree.ElementTree as ET
from collections import defaultdict

from os.path import isdir, isfile, abspath, dirname, realpath, join, basename
from typing import Optional

from arx.shell_wrapper import run_cmd, file_info, find, findw
from arx.utility import get_parent_folder


def unsparse_joiner(rawprogram0_xml: str) -> bool:
    assert isfile(rawprogram0_xml)
    work_dir = os.path.dirname(rawprogram0_xml)
    xml = ET.parse(rawprogram0_xml)
    partitions = defaultdict(list)
    for e in xml.findall("program"):
        attribs = e.attrib
        filename = attribs.get("filename")
        if filename is None:
            continue
        partitions[attribs["label"]].append(filename)
    for k, v in partitions.items():
        if len(v) > 1:
            kind = 'huawei' if '.unsparse' in v[0] else 'huawei2'
            script_path = abspath(join(dirname(realpath(__file__)), 'sh_scripts', 'combine_unsparse.sh'))
            assert isfile(script_path)
            output = run_cmd(['bash', script_path, work_dir, k, os.path.basename(rawprogram0_xml), kind])
            if output is None or len(output) <= 0:
                raise Exception('combine_unsparse.sh fail')
            newimg = join(work_dir, k + '.img')
            assert isfile(newimg)
    return True


def sparsechunks_to_raw(tmp_dir, sc_name: str) -> str:
    assert isdir(tmp_dir)
    sparse_chunks = findw(tmp_dir, f"{sc_name}.img_sparsechunk.*")
    if sparse_chunks is not None:
        sparse_chunks.sort()
        raw_img = sparse_chunks_to_raw(sc_name, sparse_chunks)
        return raw_img
    else:
        raise Exception("Flawed logic: can't find sparse chunks")


def x7z_tar_md5(file_tar_md5: str, dst_dir: str = None) -> bool:
    assert isfile(file_tar_md5)
    if dst_dir is None:
        dst_dir = get_parent_folder(file_tar_md5)
    # the following " '-o' + " is correct
    output = run_cmd(['/usr/bin/7z', 'x', file_tar_md5, '-o' + dst_dir, '-aos'])
    return "Everything is Ok" in output


def extract_lz4(img_lz4: str) -> bool:
    assert isfile(img_lz4)
    new_img = os.path.join(get_parent_folder(img_lz4), basename(img_lz4).replace('.lz4', ''))
    output = run_cmd(['/usr/bin/lz4', '--decompress', img_lz4, new_img])
    return "decoded" in output


def extract_kdz(kdz_file: str) -> bool:
    assert isfile(kdz_file)
    output_dir = get_parent_folder(kdz_file)
    script_path = abspath(join(dirname(os.path.realpath(__file__)), 'kdztools', 'unkdz.py'))
    assert isfile(script_path)
    output = run_cmd(['python3', script_path, "-f", kdz_file, "-x", "-d", output_dir])
    return "Extracting" in output


def extract_dz(dz_file: str) -> bool:
    assert isfile(dz_file)
    output_dir = get_parent_folder(dz_file)
    script_path = abspath(join(dirname(realpath(__file__)), 'kdztools', 'undz.py'))
    assert isfile(script_path)
    output = run_cmd(['python3', script_path, "-f", dz_file, "-l"])
    if output is None:
        return False
    for line in output.split("\n"):
        if "system_" in line and " : " in line:
            n = line.split(" : ")[0]
            if "/" in n:
                n = int(n.split("/")[0])
                output = run_cmd(['python3', script_path, "-f", dz_file, "-s", str(n), "-d", output_dir])
                sys_img = os.path.join(output_dir, "system.image")
                return isfile(sys_img)
    return False


def extract_update_app(update_app: str) -> bool:
    assert isfile(update_app)
    splitupdate_pl = abspath(join(dirname(realpath(__file__)), 'huawei_firmware_extractor', 'splitupdate'))
    assert isfile(splitupdate_pl)
    output = run_cmd(['perl', splitupdate_pl, update_app])
    return output is not None


def extract_sign_img(sign_img: str) -> bool:
    assert isfile(sign_img)
    parent_dir = os.path.abspath(os.path.join(sign_img, os.pardir))
    system_img = os.path.join(parent_dir, basename(sign_img).replace('-sign', ''))
    output = run_cmd(['dd', f'if={sign_img}', f'of={system_img}', 'bs=16448', 'skip=1'])
    if output is None:
        return False
    return True


def extract_br(img_dat_br: str) -> bool:
    assert isfile(img_dat_br)
    outfile = img_dat_br.replace('.br', '')
    output = run_cmd(['/usr/bin/brotli', '--decompress', '--input', img_dat_br, '--output', outfile])
    if output is None:
        return False
    ret = img_dat_br.replace('.br', '')
    assert isfile(ret)
    return "ext4 filesystem data" in file_info(ret)


def sparse_single_to_raw(img: str) -> Optional[str]:
    assert isfile(img)
    fname = basename(img)
    dir_path = os.path.dirname(img)
    raw_img = os.path.join(dir_path, f'{fname}.raw')
    output = run_cmd(['/usr/local/bin/simg2img', img, raw_img])
    if output is None:
        return None
    assert isfile(raw_img)
    return raw_img


def sparse_chunks_to_raw(sc_name: str, imgs: list) -> Optional[str]:
    assert len(imgs) > 1
    for i in imgs:
        assert isfile(i)
    dir_path = os.path.dirname(imgs[0])
    raw_img = os.path.join(dir_path, f'{sc_name}.img.raw.tmp')
    assert not isfile(raw_img)
    output = run_cmd(['/usr/local/bin/simg2img'] + imgs + [raw_img])
    if output is None:
        return None
    assert isfile(raw_img)
    with open(raw_img, 'rb') as f:
        s = f.read()
        offset = s.find(b'\x53\xEF')
        offset -= 1080
        tmp_raw = raw_img
        raw_img = tmp_raw.replace(".tmp", "")
        if offset > 0:
            output = run_cmd(['/bin/dd', f'if={tmp_raw}', f'of={raw_img}', f'ibs={offset}', 'skip=1'])
            if output is None:
                return None
        else:
            os.rename(tmp_raw, raw_img)
    assert isfile(raw_img)
    return raw_img


def extract_pac(pac_file: str) -> bool:
    assert isfile(pac_file)
    dst_dir = get_parent_folder(pac_file)
    if not dst_dir.endswith(os.sep):
        dst_dir += os.sep
    output = run_cmd(["/usr/local/bin/pacextractor", pac_file, dst_dir])
    onlyfiles = next(os.walk(dst_dir))[2]
    return len(onlyfiles) > 2


def extract_sin(img_sin: str) -> bool:
    assert isfile(img_sin)
    bin_path = abspath(join(dirname(realpath(__file__)), 'bin', 'FlashTool', 'FlashToolConsole'))
    assert isfile(bin_path)
    output = run_cmd([bin_path, "--action=extract", f'--file={img_sin}'])
    return "Extraction finished" in output


def extract_ota_payload_bin(bin_file: str, output_dir: str) -> bool:
    assert isdir(output_dir)
    assert isfile(bin_file)

    script_path = abspath(join(dirname(realpath(__file__)), 'extract_android_ota_payload', 'extract_android_ota_payload.py'))
    output = run_cmd(['python2', script_path, bin_file, output_dir])
    return output is not None


def extract_ubi_image(sys_img: str):
    assert isfile(sys_img)
    dst_dir = get_parent_folder(sys_img)
    # even if it is in Python, don't try to import it. I've warned you.
    output = run_cmd(["python3", "/usr/local/bin/ubireader_extract_files", "-o", dst_dir, sys_img])
    return "Extracting files" in output

