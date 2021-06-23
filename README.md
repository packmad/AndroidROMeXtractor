# AndroidROMeXtractor

Build the image:
```bash
docker build -t arx .
```

Local run:
```bash
docker run --rm -it --privileged=true -v "<absolute/path/on/host/ROM_name.ext>":"/DownloadedROMs/<ROM_name.ext>" arx python3 -m arx.main -i /DownloadedROMs/<ROM_name.ext>
```

Helper script for local run:
```bash
./docker_local_rom.sh <absolute/path/on/host/ROM_name.ext>
```

Run script on all files in a directory:
```bash
for f in <absolute/path/>*; do ./docker_local_rom.sh $f >> log.txt ; done
```
