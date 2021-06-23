import os
import logging
import sys

from argparse import ArgumentParser
from os.path import isfile, isdir

from arx.androidromextractor import unpack_and_mount


# create logger with 'rom_analyzer'
logger = logging.getLogger('rom_analyzer')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%d-%b-%y %H:%M:%S')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


if __name__ == "__main__":
    parser = ArgumentParser(description="AndroidROMeXtractor")
    parser.add_argument('-o', '--output', dest='dstfolder', help='Output folder')
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument('-i', '--input', dest='romfilepath', help='Input ROM file', required=True)
    args = parser.parse_args()

    in_file = args.romfilepath
    if in_file is not None:
        if not isfile(in_file):
            sys.exit("This stuff {} is not a file".format(in_file))

    dst_dir = args.dstfolder
    if dst_dir is not None and not isdir(dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
    logger.info('>>> BEGIN [unpack&mount]')
    result = unpack_and_mount(in_file, dst_dir)
    logger.info('<<< END [unpack&mount]')
    logger.info(result)
    for v in result.values():
        if isdir(v):
            logger.info(f'$ ls {v}')
            logger.info(os.listdir(v))
    logger.info('-- End ---')
