import fnmatch
import subprocess
import logging
import magic
import os
import pexpect
import shutil
import tempfile

from os.path import isfile, isdir
from typing import Optional, List

logger = logging.getLogger('rom_analyzer')


def run_cmd(cmd: List[str], env: dict = None, print_cmd: bool = True) -> Optional[str]:
    if print_cmd:
        logger.info("$ {}".format(' '.join(cmd)))
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env).strip()
        return output.decode(errors='ignore')
    except subprocess.CalledProcessError as e:
        logger.error('Error during command: {0}'.format(e.output.decode(errors='replace') if e.output else e))
        return None


def aunpack(archive: str, dstfolder: str) -> bool:
    assert isdir(dstfolder)
    assert isfile(archive)

    if "Java archive" in file_info(archive):
        from arx.formats_extraction import x7z_tar_md5  # circular dependency
        return x7z_tar_md5(archive, dstfolder)

    aunpack_path = '/usr/bin/aunpack'
    pwdtmp = tempfile.mkdtemp(dir=dstfolder)
    child = pexpect.spawn(aunpack_path, [archive, '-X', pwdtmp])
    try:
        child.expect(["Enter password", "password:"], timeout=2)
        child.close()
        child.terminate()
        # is password protected
        ret = aunpack_pwd(archive, dstfolder)
        shutil.rmtree(pwdtmp, ignore_errors=True)
        return ret      
    except Exception as e:
        pass
    # is NOT pwd protected
    output = run_cmd(["timeout", "-s", "SIGKILL", "-k", "0", "5m", aunpack_path, archive, '-X', dstfolder])
    shutil.rmtree(pwdtmp, ignore_errors=True)
    return output is not None


def aunpack_pwd(archive: str, dstfolder: str) -> bool:
    ftype = magic.from_file(archive)
    pwd = "www.stockrom.net"
    dstfolder = os.path.join(dstfolder, '')  # Ensure the path ends with a trailing slash.
    cmd = ["timeout", "-s", "SIGKILL", "-k", "0", "5m"]
    if ftype.startswith("Zip") or ftype.startswith("Java archive") or ftype.startswith("7-zip"):
        cmd += ["/usr/bin/7za", "x", archive, "-p" + pwd, "-o" + dstfolder]
        output = run_cmd(cmd)
        return "ERRORS" not in output and "No files to process" not in output
    elif ftype.startswith("RAR"):
        cmd += ["/usr/bin/unrar", "x", archive, "-p" + pwd, dstfolder]
        output = run_cmd(cmd)
        return "All OK" in output
    raise Exception("Unmanaged password protected archive '{}' of type '{}'")


def find(directory: str, tgt_file: str) -> Optional[str]:
    assert "*" not in tgt_file
    assert isdir(directory)

    for root, dirs, files in os.walk(directory):
        for file in files:
            if tgt_file == file:
                return os.path.join(root, file)
    return None


def findw(directory: str, tgt_file: str) -> Optional[list]:
    assert "*" in tgt_file
    assert isdir(directory)
    lst_match = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if fnmatch.fnmatch(file, tgt_file):
                lst_match.append(os.path.join(root, file))
    if len(lst_match) > 0:
        return lst_match
    return None


def file_info(file: str) -> Optional[str]:
    assert isfile(file)
    output = run_cmd(['/usr/bin/file', file])
    return output


def mount(img_path: str, mnt_point: str) -> bool:
    assert isfile(img_path)
    assert isdir(mnt_point)
    img_path = '"' + img_path + '"'
    output = run_cmd(['/usr/local/bin/wrapper', 'mount', img_path, mnt_point])
    logger.info('Mount output: {}'.format(output))
    return output.count('\n') == 0


def umount(mnt_dir: str) -> bool:
    assert isdir(mnt_dir)
    try:
        output = run_cmd(['/usr/local/bin/wrapper', 'umount', mnt_dir])
        return output is not None
    except Exception:
        return False


def chmodr777(dst_dir: str) -> bool:
    assert isdir(dst_dir)
    output = run_cmd(['/usr/local/bin/wrapper', 'chmod', dst_dir])
    return output is not None


def catfiles(src_files: List[str], dst_file: str) -> bool:
    cmd = "/bin/cat {} > {}".format(' '.join(src_files), dst_file)
    logger.info(f"$ {cmd}")
    os.system(cmd)
    return isfile(dst_file)


def tune2fs_block_count(img_file: str) -> str:
    output = run_cmd(['tune2fs', '-l', img_file])
    for o in output.split('\n'):
        if 'Block count' in o:
            return o.split(' ')[-1]


def resize2fs(img_file: str) -> bool:
    output = run_cmd(['resize2fs', '-f', img_file, tune2fs_block_count(img_file)])
    return output is not None


def unyaffs(img_file: str, dst_dir: str):
    assert isfile(img_file)
    assert isdir(dst_dir)
    output = run_cmd(['unyaffs', img_file, dst_dir])
