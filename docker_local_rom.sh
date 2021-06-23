#!/usr/bin/env bash

if test -f "$1"; then
    FNAME=$(basename $1)
    docker run --rm -it --privileged=true -v "$1":"/DownloadedROMs/$FNAME" arx python3 -m arx.main -i /DownloadedROMs/$FNAME
else
    echo "$1 does not exist"
fi
